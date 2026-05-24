module raijuCplHelper

    use, intrinsic :: ieee_arithmetic, only : ieee_is_finite

    use volttypes
    use raijutypes
    use remixReader
    use shellinterp
    use shellGridIO
    use shellUtils
    use ebtypes
    use raijugrids
    use ioh5
    use files
    use arrayutil
    use sami3MomentsAdapter, only : readSami3RaiCplMoments
    
    use mixdefs
    use raijuColdStartHelper, only : initRaijuColdStarter
    

    implicit none

    integer, private, parameter :: MAXIOVARS = 50

    contains

    subroutine raijuCpl_init(raiCpl, inpXML)
        class(raijuCoupler_T), intent(inout) :: raiCpl
        type(XML_Input_T), intent(inout) :: inpXML

        type(XML_Input_T) :: iXML
        character(len=strLen) :: tmpStr
        integer, dimension(4) :: shGhosts
        integer :: i
        logical :: fExist

        ! Make sure root is Kaiju/raiju
        call inpXML%GetFileStr(tmpStr)
        ! Create new XML reader w/ RAIJU as root
        iXML = New_XML_Input(trim(tmpStr),'Kaiju/RAIJU',.true.)

        ! Options
        call iXML%Set_Val(raiCpl%startup_blendTscl, "cpl/startupTscl", raiCpl%startup_blendTscl)
        call iXML%Set_Val(raiCpl%tsclSm_dL  , "cpl/tsclSm_dL"  , raiCpl%tsclSm_dL  )
        call iXML%Set_Val(raiCpl%tsclSm_dMLT, "cpl/tsclSm_dMLT", raiCpl%tsclSm_dMLT)
        call iXML%Set_Val(raiCpl%doSami3MomentsIngest, "sami3Moments/doIngest", raiCpl%doSami3MomentsIngest)
        call iXML%Set_Val(raiCpl%sami3MomentsFile, "sami3Moments/file", raiCpl%sami3MomentsFile)
        call iXML%Set_Val(raiCpl%sami3MomentsGroup, "sami3Moments/group", raiCpl%sami3MomentsGroup)
        call iXML%Set_Val(raiCpl%sami3AlphaPavg, "sami3Moments/alphaPavg", raiCpl%sami3AlphaPavg)
        call iXML%Set_Val(raiCpl%sami3AlphaDavg, "sami3Moments/alphaDavg", raiCpl%sami3AlphaDavg)
        call iXML%Set_Val(raiCpl%sami3AlphaPstd, "sami3Moments/alphaPstd", raiCpl%sami3AlphaPstd)
        call iXML%Set_Val(raiCpl%sami3AlphaDstd, "sami3Moments/alphaDstd", raiCpl%sami3AlphaDstd)
        call iXML%Set_Val(raiCpl%sami3AlphaTiote, "sami3Moments/alphaTiote", raiCpl%sami3AlphaTiote)
        call iXML%Set_Val(raiCpl%sami3DensityFloor, "sami3Moments/densityFloor", raiCpl%sami3DensityFloor)
        call iXML%Set_Val(raiCpl%sami3PressureFloor, "sami3Moments/pressureFloor", raiCpl%sami3PressureFloor)
        call iXML%Set_Val(raiCpl%sami3TioteMin, "sami3Moments/tioteMin", raiCpl%sami3TioteMin)
        call iXML%Set_Val(raiCpl%sami3TioteMax, "sami3Moments/tioteMax", raiCpl%sami3TioteMax)
        call iXML%Set_Val(raiCpl%sami3AbortOnNonfinite, "sami3Moments/abortOnNonfinite", &
            raiCpl%sami3AbortOnNonfinite)
        call sanitizeSami3MomentControls(raiCpl)
        
        ! State sub-modules that need coupler settings
        call initRaijuColdStarter(raiCpl%raiApp%Model, iXML, raiCpl%raiApp%State%coldStarter,tEndO=raiCpl%startup_blendTscl)

        ! Allocations
        associate(sh => raiCpl%raiApp%Grid%shGrid, nFluidIn => raiCpl%raiApp%Model%nFluidIn)


            ! Shell Grid inits
            shGhosts(NORTH) = sh%Ngn
            shGhosts(SOUTH) = sh%Ngs
            shGhosts(EAST)  = sh%Nge
            shGhosts(WEST)  = sh%Ngw
            call raijuGenGridFromShGrid(raiCpl%shGr, raiCpl%opt%voltGrid, iXML, raiCpl%raiApp%opt)
            call initShellVar(raiCpl%shGr, SHGR_CORNER, raiCpl%pot_total)
            call initShellVar(raiCpl%shGr, SHGR_CORNER, raiCpl%pot_corot)
            call initShellVar(raiCpl%shGr, SHGR_CC, raiCpl%bvol_cc)

            do i=1,NDIM
                call initShellVar(raiCpl%shGr, SHGR_CORNER, raiCpl%Bmin(i))
                call initShellVar(raiCpl%shGr, SHGR_CORNER, raiCpl%xyzMin(i))
                call initShellVar(raiCpl%shGr, SHGR_CC    , raiCpl%xyzMincc(i))
            enddo
            call initShellVar(raiCpl%shGr, SHGR_CORNER, raiCpl%thcon)
            call initShellVar(raiCpl%shGr, SHGR_CORNER, raiCpl%phcon)
            call initShellVar(raiCpl%shGr, SHGR_CORNER, raiCpl%bVol)
            call initShellVar(raiCpl%shGr, SHGR_CORNER, raiCpl%topo)
            call initShellVar(raiCpl%shGr, SHGR_CORNER, raiCpl%vaFrac)

            allocate(raiCpl%Pavg(0:nFluidIn))
            allocate(raiCpl%Davg(0:nFluidIn))
            allocate(raiCpl%Pstd(0:nFluidIn))
            allocate(raiCpl%Dstd(0:nFluidIn))
            do i=0,nFluidIn
                call initShellVar(raiCpl%shGr, SHGR_CC, raiCpl%Pavg(i))
                call initShellVar(raiCpl%shGr, SHGR_CC, raiCpl%Davg(i))
                call initShellVar(raiCpl%shGr, SHGR_CC, raiCpl%Pstd(i))
                call initShellVar(raiCpl%shGr, SHGR_CC, raiCpl%Dstd(i))
            enddo
            call initShellVar(raiCpl%shGr, SHGR_CC, raiCpl%tiote)
            call initShellVar(raiCpl%shGr, SHGR_CC, raiCpl%Tb)
            call initShellVar(raiCpl%shGr, SHGR_CC, raiCpl%avgBeta)

            call initShellVar(raiCpl%shGr, SHGR_CC, raiCpl%tscl_mhdIngest)
        end associate
        
        ! Initial values
        raiCpl%tLastUpdate = -1.0*HUGE
        raiCpl%pot_total%data = 0.0
        raiCpl%pot_corot%data = 0.0
        raiCpl%vaFrac%data = 0.5
        if (raiCpl%doSami3MomentsIngest) then
            inquire(file=trim(raiCpl%sami3MomentsFile), exist=fExist)
            if (.not. fExist) then
                write(*,*) "SAMI3 moments ingest requested but file is missing: ", trim(raiCpl%sami3MomentsFile)
                stop
            endif
            write(*,*) "SAMI3 moments ingest enabled: ", trim(raiCpl%sami3MomentsFile), " group=", trim(raiCpl%sami3MomentsGroup)
            write(*,*) "SAMI3 moments alpha Pavg/Davg/Pstd/Dstd/tiote:", &
                raiCpl%sami3AlphaPavg, raiCpl%sami3AlphaDavg, raiCpl%sami3AlphaPstd, &
                raiCpl%sami3AlphaDstd, raiCpl%sami3AlphaTiote
            write(*,*) "SAMI3 moments floors density/pressure and tiote min/max:", &
                raiCpl%sami3DensityFloor, raiCpl%sami3PressureFloor, &
                raiCpl%sami3TioteMin, raiCpl%sami3TioteMax
            write(*,*) "SAMI3 moments abortOnNonfinite:", raiCpl%sami3AbortOnNonfinite
        endif

    end subroutine raijuCpl_init


    subroutine applySami3RaiCplMoments(raiCpl)
        class(raijuCoupler_T), intent(inout) :: raiCpl

        real(rp), dimension(:,:,:), allocatable :: Pavg0, Davg0, Pstd0, Dstd0
        real(rp), dimension(:,:), allocatable :: tiote0
        logical, dimension(:,:,:), allocatable :: PavgMask0, DavgMask0, PstdMask0, DstdMask0
        logical, dimension(:,:,:), allocatable :: PavgUseMask, DavgUseMask, PstdUseMask, DstdUseMask
        logical, dimension(:,:), allocatable :: tioteMask0
        logical, dimension(:,:), allocatable :: tioteUseMask
        integer :: i0, i1, j0, j1, k0, k1, k
        logical :: fExist

        if (.not. raiCpl%doSami3MomentsIngest) return

        inquire(file=trim(raiCpl%sami3MomentsFile), exist=fExist)
        if (.not. fExist) then
            write(*,*) "SAMI3 moments ingest requested but file is missing: ", trim(raiCpl%sami3MomentsFile)
            stop
        endif

        k0 = lbound(raiCpl%Pavg,1)
        k1 = ubound(raiCpl%Pavg,1)
        i0 = lbound(raiCpl%Pavg(k0)%data,1)
        i1 = ubound(raiCpl%Pavg(k0)%data,1)
        j0 = lbound(raiCpl%Pavg(k0)%data,2)
        j1 = ubound(raiCpl%Pavg(k0)%data,2)

        allocate(Pavg0(i0:i1,j0:j1,k0:k1))
        allocate(Davg0(i0:i1,j0:j1,k0:k1))
        allocate(Pstd0(i0:i1,j0:j1,k0:k1))
        allocate(Dstd0(i0:i1,j0:j1,k0:k1))
        allocate(PavgMask0(i0:i1,j0:j1,k0:k1))
        allocate(DavgMask0(i0:i1,j0:j1,k0:k1))
        allocate(PstdMask0(i0:i1,j0:j1,k0:k1))
        allocate(DstdMask0(i0:i1,j0:j1,k0:k1))
        allocate(PavgUseMask(i0:i1,j0:j1,k0:k1))
        allocate(DavgUseMask(i0:i1,j0:j1,k0:k1))
        allocate(PstdUseMask(i0:i1,j0:j1,k0:k1))
        allocate(DstdUseMask(i0:i1,j0:j1,k0:k1))
        do k=k0,k1
            Pavg0(:,:,k) = raiCpl%Pavg(k)%data
            Davg0(:,:,k) = raiCpl%Davg(k)%data
            Pstd0(:,:,k) = raiCpl%Pstd(k)%data
            Dstd0(:,:,k) = raiCpl%Dstd(k)%data
            PavgMask0(:,:,k) = raiCpl%Pavg(k)%mask
            DavgMask0(:,:,k) = raiCpl%Davg(k)%mask
            PstdMask0(:,:,k) = raiCpl%Pstd(k)%mask
            DstdMask0(:,:,k) = raiCpl%Dstd(k)%mask
        enddo

        allocate(tiote0(lbound(raiCpl%tiote%data,1):ubound(raiCpl%tiote%data,1), &
            lbound(raiCpl%tiote%data,2):ubound(raiCpl%tiote%data,2)))
        allocate(tioteMask0(lbound(raiCpl%tiote%mask,1):ubound(raiCpl%tiote%mask,1), &
            lbound(raiCpl%tiote%mask,2):ubound(raiCpl%tiote%mask,2)))
        allocate(tioteUseMask(lbound(raiCpl%tiote%mask,1):ubound(raiCpl%tiote%mask,1), &
            lbound(raiCpl%tiote%mask,2):ubound(raiCpl%tiote%mask,2)))
        tiote0 = raiCpl%tiote%data
        tioteMask0 = raiCpl%tiote%mask

        call readSami3RaiCplMoments(raiCpl, trim(raiCpl%sami3MomentsFile), trim(raiCpl%sami3MomentsGroup))

        do k=k0,k1
            PavgUseMask(:,:,k) = raiCpl%Pavg(k)%mask
            DavgUseMask(:,:,k) = raiCpl%Davg(k)%mask
            PstdUseMask(:,:,k) = raiCpl%Pstd(k)%mask
            DstdUseMask(:,:,k) = raiCpl%Dstd(k)%mask
        enddo
        tioteUseMask = raiCpl%tiote%mask

        do k=k0,k1
            raiCpl%Pavg(k)%mask = PavgMask0(:,:,k)
            raiCpl%Davg(k)%mask = DavgMask0(:,:,k)
            raiCpl%Pstd(k)%mask = PstdMask0(:,:,k)
            raiCpl%Dstd(k)%mask = DstdMask0(:,:,k)
            call blendFloorSami3Moment(raiCpl%Pavg(k)%data, Pavg0(:,:,k), &
                PavgUseMask(:,:,k), &
                raiCpl%sami3AlphaPavg, raiCpl%sami3PressureFloor, "Pavg", k, &
                raiCpl%sami3AbortOnNonfinite)
            call blendFloorSami3Moment(raiCpl%Davg(k)%data, Davg0(:,:,k), &
                DavgUseMask(:,:,k), &
                raiCpl%sami3AlphaDavg, raiCpl%sami3DensityFloor, "Davg", k, &
                raiCpl%sami3AbortOnNonfinite)
            call blendFloorSami3Moment(raiCpl%Pstd(k)%data, Pstd0(:,:,k), &
                PstdUseMask(:,:,k), &
                raiCpl%sami3AlphaPstd, 0.0_rp, "Pstd", k, raiCpl%sami3AbortOnNonfinite)
            call blendFloorSami3Moment(raiCpl%Dstd(k)%data, Dstd0(:,:,k), &
                DstdUseMask(:,:,k), &
                raiCpl%sami3AlphaDstd, 0.0_rp, "Dstd", k, raiCpl%sami3AbortOnNonfinite)
        enddo
        raiCpl%tiote%mask = tioteMask0
        call blendClampSami3Moment(raiCpl%tiote%data, tiote0, raiCpl%sami3AlphaTiote, &
            tioteUseMask, raiCpl%sami3TioteMin, raiCpl%sami3TioteMax, "tiote", &
            raiCpl%sami3AbortOnNonfinite)

        if (.not. raiCpl%sami3MomentsReported) then
            write(*,*) "SAMI3 moments ingest applied after RAIJU realtime pack: ", &
                trim(raiCpl%sami3MomentsFile), " group=", trim(raiCpl%sami3MomentsGroup)
            write(*,*) "SAMI3 moments Pavg(0) min/max:", minval(raiCpl%Pavg(0)%data), maxval(raiCpl%Pavg(0)%data)
            write(*,*) "SAMI3 moments Davg(0) min/max:", minval(raiCpl%Davg(0)%data), maxval(raiCpl%Davg(0)%data)
            write(*,*) "SAMI3 moments tiote min/max:", minval(raiCpl%tiote%data), maxval(raiCpl%tiote%data)
            write(*,*) "SAMI3 moments valid mask counts Pavg/Davg/Pstd/Dstd/tiote:", &
                count(PavgUseMask), count(DavgUseMask), count(PstdUseMask), count(DstdUseMask), &
                count(tioteUseMask)
            raiCpl%sami3MomentsReported = .true.
        endif

    end subroutine applySami3RaiCplMoments


    subroutine sanitizeSami3MomentControls(raiCpl)
        class(raijuCoupler_T), intent(inout) :: raiCpl

        raiCpl%sami3AlphaPavg = clamp01(raiCpl%sami3AlphaPavg)
        raiCpl%sami3AlphaDavg = clamp01(raiCpl%sami3AlphaDavg)
        raiCpl%sami3AlphaPstd = clamp01(raiCpl%sami3AlphaPstd)
        raiCpl%sami3AlphaDstd = clamp01(raiCpl%sami3AlphaDstd)
        raiCpl%sami3AlphaTiote = clamp01(raiCpl%sami3AlphaTiote)
        raiCpl%sami3DensityFloor = max(0.0_rp, raiCpl%sami3DensityFloor)
        raiCpl%sami3PressureFloor = max(0.0_rp, raiCpl%sami3PressureFloor)
        raiCpl%sami3TioteMin = max(0.0_rp, raiCpl%sami3TioteMin)
        raiCpl%sami3TioteMax = max(raiCpl%sami3TioteMin, raiCpl%sami3TioteMax)
    end subroutine sanitizeSami3MomentControls


    real(rp) function clamp01(x)
        real(rp), intent(in) :: x

        clamp01 = min(1.0_rp, max(0.0_rp, x))
    end function clamp01


    subroutine blendFloorSami3Moment(data, baseData, inputMask, alpha, floorVal, fieldName, channel, abortOnBad)
        real(rp), dimension(:,:), intent(inout) :: data
        real(rp), dimension(:,:), intent(in) :: baseData
        logical, dimension(:,:), intent(in) :: inputMask
        real(rp), intent(in) :: alpha, floorVal
        character(len=*), intent(in) :: fieldName
        integer, intent(in) :: channel
        logical, intent(in) :: abortOnBad

        integer :: nBad

        if (alpha <= 0.0_rp) then
            data = baseData
        else
            nBad = count(inputMask .and. (.not. ieee_is_finite(data)))
            if (nBad > 0) then
                write(*,*) "SAMI3 moments non-finite input: ", trim(fieldName), &
                    " channel=", channel, " count=", nBad
                if (abortOnBad) stop
                where (inputMask .and. (.not. ieee_is_finite(data)))
                    data = baseData
                end where
            endif
            if (alpha < 1.0_rp) then
                where (inputMask)
                    data = (1.0_rp-alpha)*baseData + alpha*data
                elsewhere
                    data = baseData
                end where
            else
                where (.not. inputMask)
                    data = baseData
                end where
            endif
        endif
        where (inputMask .and. (data < floorVal))
            data = floorVal
        end where
    end subroutine blendFloorSami3Moment


    subroutine blendClampSami3Moment(data, baseData, alpha, inputMask, minVal, maxVal, fieldName, abortOnBad)
        real(rp), dimension(:,:), intent(inout) :: data
        real(rp), dimension(:,:), intent(in) :: baseData
        logical, dimension(:,:), intent(in) :: inputMask
        real(rp), intent(in) :: alpha, minVal, maxVal
        character(len=*), intent(in) :: fieldName
        logical, intent(in) :: abortOnBad

        integer :: nBad

        if (alpha <= 0.0_rp) then
            data = baseData
        else
            nBad = count(inputMask .and. (.not. ieee_is_finite(data)))
            if (nBad > 0) then
                write(*,*) "SAMI3 moments non-finite input: ", trim(fieldName), " count=", nBad
                if (abortOnBad) stop
                where (inputMask .and. (.not. ieee_is_finite(data)))
                    data = baseData
                end where
            endif
            if (alpha < 1.0_rp) then
                where (inputMask)
                    data = (1.0_rp-alpha)*baseData + alpha*data
                elsewhere
                    data = baseData
                end where
            else
                where (.not. inputMask)
                    data = baseData
                end where
            endif
        endif
        where (inputMask .and. (data < minVal))
            data = minVal
        end where
        where (inputMask .and. (data > maxVal))
            data = maxVal
        end where
    end subroutine blendClampSami3Moment


    subroutine tubeShell2RaiCpl(voltGrid, tubeShell, raiCpl)
        !! Takes voltron tubeShell data and stores what we need into our coupler
        !! Using the shell interp, we are mapping some quantities from corners to centers as expected by raijuApp
        type(ShellGrid_T), intent(in) :: voltGrid
        type(TubeShell_T), intent(in) :: tubeShell
        class(raijuCoupler_T), intent(inout) :: raiCpl

        type(ShellGridVar_T) :: tmpTopo
        logical, dimension(tubeShell%topo%isv:tubeShell%topo%iev,tubeShell%topo%jsv:tubeShell%topo%jev) :: topoSrcMask
        integer :: i,j,s

        where (tubeShell%topo%data == TUBE_CLOSED)
            topoSrcMask = .true.
        elsewhere
            topoSrcMask = .false.
        end where

        call initShellVar(raiCpl%shGr, SHGR_CORNER, tmpTopo)

        ! Corners
        do i=1,NDIM
            call InterpShellVar_TSC_SG(voltGrid, tubeShell%X_bmin(i), raiCpl%shGr, raiCpl%xyzMin(i))
        enddo
        call InterpShellVar_TSC_SG(voltGrid, tubeShell%bmin, raiCpl%shGr, raiCpl%Bmin(ZDIR))
        call InterpShellVar_TSC_SG(voltGrid, tubeShell%latc, raiCpl%shGr, raiCpl%thcon)
        raiCpl%thcon%data = PI/2 - raiCpl%thcon%data
        call InterpShellVar_TSC_SG(voltGrid, tubeShell%lonc, raiCpl%shGr, raiCpl%phcon)
        call InterpShellVar_TSC_SG(voltGrid, tubeShell%bVol, raiCpl%shGr, raiCpl%bvol)
        !call InterpShellVar_ParentToChild(voltGrid, tubeShell%bVol, raiCpl%shGr, raiCpl%bvol)
        !call InterpShellVar_TSC_SG(voltGrid, tubeShell%bVol, raiCpl%shGr, raiCpl%bvol_cc)
        do j=raiCpl%shGr%jsg,raiCpl%shGr%jeg
            do i=raiCpl%shGr%isg,raiCpl%shGr%ieg
                raiCpl%bvol_cc%data(i,j) = toCenter2D(raiCpl%bvol%data(i:i+1,j:j+1))
            enddo
        enddo
        
        ! Get topo and then convert to RAIJU's definition
        call InterpShellVar_TSC_SG(voltGrid, tubeShell%topo, raiCpl%shGr, tmpTopo)
        where (abs(tmpTopo%data - TUBE_CLOSED) < TINY)
            raiCpl%topo%data = RAIJUCLOSED
        elsewhere
            raiCpl%topo%data = RAIJUOPEN
        end where
        call InterpShellVar_TSC_SG(voltGrid, tubeShell%wMAG, raiCpl%shGr, raiCpl%vaFrac)

        ! Centers
        do s=0,raiCpl%raiApp%Model%nFluidIn
            call InterpShellVar_TSC_SG(voltGrid, tubeShell%avgP(s), raiCpl%shGr, raiCpl%Pavg(s), srcMaskO=topoSrcMask)
            call InterpShellVar_TSC_SG(voltGrid, tubeShell%avgN(s), raiCpl%shGr, raiCpl%Davg(s), srcMaskO=topoSrcMask)
            call InterpShellVar_TSC_SG(voltGrid, tubeShell%stdP(s), raiCpl%shGr, raiCpl%Pstd(s), srcMaskO=topoSrcMask)
            call InterpShellVar_TSC_SG(voltGrid, tubeShell%stdN(s), raiCpl%shGr, raiCpl%Dstd(s), srcMaskO=topoSrcMask)
        enddo
        call InterpShellVar_TSC_SG(voltGrid, tubeShell%TioTe0, raiCpl%shGr, raiCpl%tiote)
        do i=1,NDIM
            call InterpShellVar_TSC_SG(raiCpl%shGr, raiCpl%xyzMin(i), raiCpl%shGr, raiCpl%xyzMincc(i), srcMaskO=topoSrcMask)
        enddo
        call InterpShellVar_TSC_SG(voltGrid, tubeShell%Tb     , raiCpl%shGr, raiCpl%Tb     , srcMaskO=topoSrcMask)
        call InterpShellVar_TSC_SG(voltGrid, tubeShell%avgBeta, raiCpl%shGr, raiCpl%avgBeta, srcMaskO=topoSrcMask)

    end subroutine tubeShell2RaiCpl


    subroutine raiCpl2RAIJU(raiCpl)
        !! Take info at raijuCoupler level and put it into RAIJU proper
        !! raiCpl should have everything in the sizes we expect, so just need to do a bunch of copies
        class(raijuCoupler_T), intent(inout) :: raiCpl

        integer :: i,j,k
    
        associate(Model=>raiCpl%raiApp%Model, State=>raiCpl%raiApp%State, shGr=>raiCpl%shGr)

        ! Reset quantities we will only selectively write to
        State%Pavg = 0
        State%Davg = 0
        State%Pstd = 0
        State%Dstd = 0
        State%bvol_cc = 0
        State%Tb%data = 0

        !--- Ionosphere data ---!
        State%espot(:,:)     = raiCpl%pot_total%data(:,:) ! They live on the same grid so this is okay
        State%pot_corot(:,:) = raiCpl%pot_corot%data(:,:)


        !--- Mag data ---!

        ! Defaults
        State%Tb%data = HUGE

        State%topo = raiCpl%topo%data

        ! Copy no matter the topo value
        do i=1,NDIM
            State%xyzMin  (:,:,i) = raiCpl%xyzMin(i)%data
            State%xyzMincc(:,:,i) = raiCpl%xyzMincc(i)%data
        enddo
        State%thcon(:,:)     = raiCpl%thcon%data
        State%phcon(:,:)     = raiCpl%phcon%data
        State%Bmin(:,:,ZDIR) = raiCpl%bmin(ZDIR)%data
        State%bvol(:,:)      = raiCpl%bvol%data
        State%vaFrac(:,:)    = raiCpl%vaFrac%data

        ! Now only copy for good points
        !$OMP PARALLEL DO default(shared) &
        !$OMP schedule(dynamic) &
        !$OMP private(i,j)
        do j=shGr%jsg,shGr%jeg
            do i=shGr%isg,shGr%ieg

                if (any(State%topo(i:i+1,j:j+1) .eq. RAIJUOPEN)) then
                    cycle
                endif

                do k=0,Model%nFluidIn
                    State%Pavg(i,j,k) = raiCpl%Pavg(k)%data(i,j)
                    State%Davg(i,j,k) = raiCpl%Davg(k)%data(i,j)
                    State%Pstd(i,j,k) = raiCpl%Pstd(k)%data(i,j) / max(State%Pavg(i,j,k), TINY)  ! Normalize
                    State%Dstd(i,j,k) = raiCpl%Dstd(k)%data(i,j) / max(State%Davg(i,j,k), TINY)
                enddo

                State%bvol_cc(i,j) = raiCpl%bvol_cc%data(i,j)
                State%tiote(i,j) = raiCpl%tiote%data(i,j)
                State%Tb%data(i,j) = raiCpl%Tb%data(i,j)
            enddo
        enddo

        end associate
    end subroutine

!------
! Real-time coupling stuff
!------

    subroutine packRaijuCoupler_RT(raiCpl, vApp)
        class(raijuCoupler_T), intent(inout) :: raiCpl
        class(voltApp_T), intent(in) :: vApp

        raiCpl%tLastUpdate = vApp%time

        !call genImagTubes(raiCpl, vApp)
        call tubeShell2RaiCpl(vApp%shGrid, vApp%State%tubeShell, raiCpl)
        call applySami3RaiCplMoments(raiCpl)
        !call mixPot2Raiju_RT(raiCpl, vApp%remixApp)
        
        call InterpShellVar_ParentToChild(vApp%shGrid, vApp%State%potential_total, raiCpl%shGr, raiCpl%pot_total)
        call InterpShellVar_ParentToChild(vApp%shGrid, vApp%State%potential_corot, raiCpl%shGr, raiCpl%pot_corot)
        
    end subroutine


!------
! Post-advance calculations
!------

    subroutine raiCpl_PostAdvance(raiCpl)
        class(raijuCoupler_T), intent(inout) :: raiCpl

        call raiCpl_calcTsclMHD(raiCpl)
    end subroutine raiCpl_PostAdvance


    subroutine raiCpl_calcTsclMHD(raiCpl)
        class(raijuCoupler_T), intent(inout) :: raiCpl

        integer :: i,j
        real(rp) :: vaFrac_cc
        
        associate(tscl=>raiCpl%tscl_mhdIngest, State=>raiCpl%raiApp%State, sh=>raiCpl%shGr)

        ! Defaults
        call fillArray(tscl%data, State%dt)
        where (State%active /= RAIJUINACTIVE)
            tscl%mask = .true.
        elsewhere
            tscl%mask = .false.
        end where

        ! First, calculate our tscl point-by-point
        !$OMP PARALLEL DO default(shared) &
        !$OMP private(i,j,vaFrac_cc)
        do j=sh%jsg,sh%jeg
            do i=sh%isg,sh%ieg
                if (tscl%mask(i,j)) then
                    vaFrac_cc = 0.25*sum(State%vaFrac(i:i+1,j:j+1))
                    tscl%data(i,j) = raiCpl%raiApp%Model%nBounce*State%dt/(vaFrac_cc)**2 
                endif
            enddo
        enddo

        ! Now do smoothing
        call smoothRaijuVar_eq(State, sh, raiCpl%tsclSm_dMLT, raiCpl%tsclSm_dL, tscl)

        ! We had the mask include buffer cells for smoothing reasons, but now we want anyone interpolating to only use active cells
        where (State%active == RAIJUACTIVE)
            tscl%mask = .true.
        elsewhere
            tscl%mask = .false.
        end where

        end associate


        contains

        subroutine smoothRaijuVar_eq(State, sh, dMLT, dL, var)
            !! Smooth a raiju variable with stencil in equatorial projection
            type(raijuState_T), intent(in) :: State
            type(ShellGrid_T), intent(in) :: sh
            real(rp), intent(in) :: dMLT
            real(rp), intent(in) :: dL
            type(ShellGridVar_T), intent(inout) :: var
                !! Variable to smooth. Assumes var%mask can be used to include/exclude points

            integer :: i, j, j_eval, ipnt, jpnt
            integer :: dj, dj_half, nGood
            logical :: doIScan
            real(rp) :: var_sum
            real(rp) :: L_center, L_pnt
            real(rp) :: dPhi_rad, dMLT_pnt, dL_pnt
            real(rp), dimension(:,:), allocatable :: tmp_var_sm

            
            if (.not. sh%isPhiUniform) then
                write(*,*) "ERROR: raiCpl_calcTsclMHD expects raiCpl ShellGrid to have periodic phi, but it does not"
                write(*,*) "  Goodbye."
                stop
            endif

            if (var%loc /= SHGR_CC ) then
                write(*,*) "ERROR: raiCpl_calcTsclMHD expects raiCpl ShellGridVar to be located at cell center"
                write(*,*) "  Given var with location enum:",var%loc
                write(*,*) "  Goodbye."
                stop
            endif

            allocate(tmp_var_sm(var%isv:var%iev, var%jsv:var%jev))
            call fillArray(tmp_var_sm, 0.0_rp)

            dphi_rad = dMLT * PI/12.0_rp  ! Convert delta-MLT to a delta-phi in radians
            dj_half = 0
            do while(sh%ph(sh%js + dj_half + 1) - sh%phc(sh%js) < dphi_rad/2.0_rp)  ! Increase dj_half until its dphi is half of target dphi_rad (you're welcome)
                dj_half = dj_half + 1
            enddo

            !$OMP PARALLEL DO default(shared) &
            !$OMP schedule(dynamic) &
            !$OMP private(i, j, dj, doIScan) &
            !$OMP private(nGood, var_sum, ipnt, jpnt, L_center, L_pnt, dL_pnt)
            do j=sh%jsg,sh%jeg
                do i=sh%isg,sh%ieg
                    if (.not. var%mask(i,j)) then
                        cycle
                    endif

                    L_center = norm2(State%xyzMincc(i,j,XDIR:YDIR))  ! XY plane to L shell / radius from planet

                    nGood = 0
                    var_sum = 0.0_rp
                    ! Loop over j stencil range
                    do dj=-dj_half,dj_half
                        jpnt = j + dj
                        if (jpnt < sh%js) then
                            jpnt = jpnt + sh%Np
                        elseif (jpnt > sh%je) then
                            jpnt = jpnt - sh%Np
                        endif

                        ! Sweep in i+ direction (earthward)
                        doIScan = .true.
                        ipnt = i
                        do while (doIScan)
                            L_pnt = norm2(State%xyzMincc(ipnt,jpnt,XDIR:YDIR))
                            dL_pnt = abs(L_center  - L_pnt)

                            ! First decide if we are gonna keep going after this point
                            if (ipnt >= sh%ieg .or. dL_pnt > dL/2.0_rp) then
                                doIScan = .false.
                            endif

                            ! Decide if we should include this point
                            if (var%mask(ipnt,jpnt) .and. (dL_pnt < dL/2.0_rp)) then
                                nGood = nGood + 1
                                var_sum = var_sum + var%data(ipnt,jpnt)
                            endif
                            ipnt = ipnt + 1
                        enddo

                        ! Same thing but in the -i direction
                        doIScan = .true.
                        ipnt = i-1
                        do while(doIScan)
                            L_pnt = norm2(State%xyzMincc(ipnt,jpnt,XDIR:YDIR))
                            dL_pnt = abs(L_center  - L_pnt)

                            if (ipnt <= sh%isg .or. dL_pnt > dL/2.0_rp) then
                                doIScan = .false.
                            endif

                            if (var%mask(ipnt,jpnt) .and. (dL_pnt < dL/2.0_rp)) then
                                nGood = nGood + 1
                                var_sum = var_sum + var%data(ipnt,jpnt)
                            endif
                            ipnt = ipnt - 1
                        enddo
                    enddo

                    ! Now calculate and save our average
                    if (nGood > 0) then
                        tmp_var_sm(i,j) = var_sum/(1.0_rp*nGood)
                    endif
                enddo
            enddo

            ! Put it back into the original variable and we're done
            var%data(:,:) = tmp_var_sm(:,:)

        end subroutine smoothRaijuVar_eq

    end subroutine raiCpl_calcTsclMHD


!------
! Coupler I/O
!------

    subroutine writeRaiCplRes(raiCpl, nRes)
        class(raijuCoupler_T), intent(in) :: raiCpl
        integer, intent(in) :: nRes

        character(len=strLen) :: ResF,lnResF !Name of restart file
        !logical :: fExist
        type(IOVAR_T), dimension(MAXIOVARS) :: IOVars

        write (ResF  , '(A,A,I0.5,A)') trim(raiCpl%raiApp%Model%RunID), ".raiCpl.Res.", nRes   , ".h5"
        write (lnResF, '(A,A,A,A)'   ) trim(raiCpl%raiApp%Model%RunID), ".raiCpl.Res.", "XXXXX", ".h5"
        call CheckAndKill(ResF)     
        
        call writeShellGrid(raiCpl%shGr, ResF,"/ShellGrid")

        call ClearIO(IOVars)
        call AddOutVar(IOVars, "tLastUpdate"   , raiCpl%tLastUpdate   , uStr="s")
        call AddOutSGV(IOVars, "Pavg"          , raiCpl%Pavg          , doWriteMaskO=.true.)
        call AddOutSGV(IOVars, "Davg"          , raiCpl%Davg          , doWriteMaskO=.true.)
        call AddOutSGV(IOVars, "Pstd"          , raiCpl%Pstd          , doWriteMaskO=.true.)
        call AddOutSGV(IOVars, "Dstd"          , raiCpl%Dstd          , doWriteMaskO=.true.)
        call AddOutSGV(IOVars, "Bmin"          , raiCpl%Bmin          , doWriteMaskO=.true.)
        call AddOutSGV(IOVars, "xyzMin"        , raiCpl%xyzMin        , doWriteMaskO=.true.)
        call AddOutSGV(IOVars, "xyzMincc"      , raiCpl%xyzMincc      , doWriteMaskO=.true.)
        call AddOutSGV(IOVars, "topo"          , raiCpl%topo          , doWriteMaskO=.true.)
        call AddOutSGV(IOVars, "thcon"         , raiCpl%thcon         , doWriteMaskO=.true.)
        call AddOutSGV(IOVars, "phcon"         , raiCpl%phcon         , doWriteMaskO=.true.)
        call AddOutSGV(IOVars, "bvol"          , raiCpl%bvol          , doWriteMaskO=.true.)
        call AddOutSGV(IOVars, "bvol_cc"       , raiCpl%bvol_cc       , doWriteMaskO=.true.)
        call AddOutSGV(IOVars, "vaFrac"        , raiCpl%vaFrac        , doWriteMaskO=.true.)
        call AddOutSGV(IOVars, "Tb"            , raiCpl%Tb            , doWriteMaskO=.true.)
        call AddOutSGV(IOVars, "pot_total"     , raiCpl%pot_total     , doWriteMaskO=.true.)
        call AddOutSGV(IOVars, "pot_corot"     , raiCpl%pot_corot     , doWriteMaskO=.true.)
        call AddOutSGV(IOVars, "tscl_mhdIngest", raiCpl%tscl_mhdIngest, doWriteMaskO=.true.)
        call WriteVars(IOVars, .false., ResF)
        call MapSymLink(ResF,lnResF)
    end subroutine


    subroutine readRaiCplRes(raiCpl, resId, nRes)
        class(raijuCoupler_T), intent(inout) :: raiCpl
        character(len=*), intent(in) :: resId
        integer, intent(in) :: nRes

        character(len=strLen) :: ResF, nStr
        type(IOVAR_T), dimension(MAXIOVARS) :: IOVars

        if (nRes == -1) then
            nStr = "XXXXX"
        else
            write(nStr,'(I0.5)') nRes
        endif
        write(ResF,'(A,A,A,A)')trim(resId),".raiCpl.Res.",trim(nStr),".h5"

        call GenShellGridFromFile(raiCpl%shGr, "RAIJU", ResF,"/ShellGrid")

        call ClearIO(IOVars)
        call AddInVar(IOVars, "tLastUpdate",vTypeO=IOREAL)
        call ReadVars(IOVars, .false., ResF)
        raiCpl%tLastUpdate = GetIOReal(IOVars, "tLastUpdate")

        ! ShellGridVars
        call ReadInSGV(raiCpl%Pavg          ,ResF, "Pavg"          , doIOpO=.false.)
        call ReadInSGV(raiCpl%Davg          ,ResF, "Davg"          , doIOpO=.false.)
        call ReadInSGV(raiCpl%Pstd          ,ResF, "Pstd"          , doIOpO=.false.)
        call ReadInSGV(raiCpl%Dstd          ,ResF, "Dstd"          , doIOpO=.false.)
        call ReadInSGV(raiCpl%Bmin          ,ResF, "Bmin"          , doIOpO=.false.)
        call ReadInSGV(raiCpl%xyzMin        ,ResF, "xyzMin"        , doIOpO=.false.)
        call ReadInSGV(raiCpl%xyzMincc      ,ResF, "xyzMincc"      , doIOpO=.false.)
        call ReadInSGV(raiCpl%topo          ,ResF, "topo"          , doIOpO=.false.)
        call ReadInSGV(raiCpl%thcon         ,ResF, "thcon"         , doIOpO=.false.)
        call ReadInSGV(raiCpl%phcon         ,ResF, "phcon"         , doIOpO=.false.)
        call ReadInSGV(raiCpl%bvol          ,ResF, "bvol"          , doIOpO=.false.)
        call ReadInSGV(raiCpl%bvol_cc       ,ResF, "bvol_cc"       , doIOpO=.false.)
        call ReadInSGV(raiCpl%vaFrac        ,ResF, "vaFrac"        , doIOpO=.false.)
        call ReadInSGV(raiCpl%Tb            ,ResF, "Tb"            , doIOpO=.false.)
        call ReadInSGV(raiCpl%pot_total     ,ResF, "pot_total"     , doIOpO=.false.)
        call ReadInSGV(raiCpl%pot_corot     ,ResF, "pot_corot"     , doIOpO=.false.)
        call ReadInSGV(raiCpl%tscl_mhdIngest,ResF, "tscl_mhdIngest", doIOpO=.false.)

    end subroutine

end module raijuCplHelper
