module sami3MomentsAdapter
    !! Minimal read hooks for SAMI3 moments-only HDF5 products.
    !!
    !! These routines deliberately read only the existing MAGE moments fields:
    !! Pavg/Davg/Pstd/Dstd/tiote for RAIJU and avgP/avgN/stdP/stdN/Tiote0
    !! for TubeShell.  They do not read a complete restart and do not alter
    !! GAMERA equations.

    use kdefs,       only : strLen
    use shellGridIO, only : ReadInSGV
    use voltCplTypes, only : TubeShell_T
    use volttypes,   only : raijuCoupler_T

    implicit none

    private
    public :: readSami3TubeShellMoments
    public :: readSami3RaiCplMoments

contains

    subroutine readSami3TubeShellMoments(tubeShell, ResF, gStrO)
        !! Read only TubeShell moment fields from a SAMI3 moments diagnostic.
        !!
        !! Expected default group:
        !!   /TubeShellMomentsOnly
        !!
        !! The caller must initialize tubeShell and its ShellGridVars before
        !! calling this routine.  The input group must use the fixed
        !! MAXTUBEFLUIDS+1 channel layout used by TubeShell_T.
        type(TubeShell_T), intent(inout) :: tubeShell
        character(len=*), intent(in) :: ResF
        character(len=*), intent(in), optional :: gStrO

        character(len=strLen) :: gStr

        if (present(gStrO)) then
            gStr = trim(gStrO)
        else
            gStr = "/TubeShellMomentsOnly"
        endif

        call ReadInSGV(tubeShell%avgP  , ResF, "avgP"  , gStrO=gStr, doIOpO=.false.)
        call ReadInSGV(tubeShell%avgN  , ResF, "avgN"  , gStrO=gStr, doIOpO=.false.)
        call ReadInSGV(tubeShell%stdP  , ResF, "stdP"  , gStrO=gStr, doIOpO=.false.)
        call ReadInSGV(tubeShell%stdN  , ResF, "stdN"  , gStrO=gStr, doIOpO=.false.)
        call ReadInSGV(tubeShell%TioTe0, ResF, "Tiote0", gStrO=gStr, doIOpO=.false.)
    end subroutine readSami3TubeShellMoments


    subroutine readSami3RaiCplMoments(raiCpl, ResF, gStrO)
        !! Read only raijuCoupler_T moment fields from a SAMI3 moments diagnostic.
        !!
        !! Expected default group:
        !!   /RaiCplMomentsOnly
        !!
        !! The caller must initialize raiCpl and its ShellGridVars before
        !! calling this routine.  Pstd/Dstd are read as absolute values; the
        !! existing raiCpl2RAIJU path normalizes them when copying into RAIJU
        !! State.
        class(raijuCoupler_T), intent(inout) :: raiCpl
        character(len=*), intent(in) :: ResF
        character(len=*), intent(in), optional :: gStrO

        character(len=strLen) :: gStr

        if (present(gStrO)) then
            gStr = trim(gStrO)
        else
            gStr = "/RaiCplMomentsOnly"
        endif

        call ReadInSGV(raiCpl%Pavg , ResF, "Pavg" , gStrO=gStr, doIOpO=.false.)
        call ReadInSGV(raiCpl%Davg , ResF, "Davg" , gStrO=gStr, doIOpO=.false.)
        call ReadInSGV(raiCpl%Pstd , ResF, "Pstd" , gStrO=gStr, doIOpO=.false.)
        call ReadInSGV(raiCpl%Dstd , ResF, "Dstd" , gStrO=gStr, doIOpO=.false.)
        call ReadInSGV(raiCpl%tiote, ResF, "tiote", gStrO=gStr, doIOpO=.false.)
    end subroutine readSami3RaiCplMoments

end module sami3MomentsAdapter
