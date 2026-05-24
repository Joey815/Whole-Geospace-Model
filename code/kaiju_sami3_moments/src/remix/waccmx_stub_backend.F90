module waccmx_stub_backend
  use iso_fortran_env, only: int32, real32
  use ieee_arithmetic, only: ieee_is_finite
  use gcmtypes
  use mixdefs
  use mixtypes
  use math
  use ioH5
  use waccmx_stub_feedback_io

  implicit none

  integer, parameter :: MAXIOVAR = 32
  integer(int32), parameter :: sami3_phi_magic = 20260524_int32
  integer(int32), parameter :: sami3_phi_version = 1_int32
  integer, parameter :: sami3_phi_nlat = 125
  integer, parameter :: sami3_phi_nlon = 97
  real(rp), parameter :: statvolt_per_kv = 1000.0_rp/300.0_rp
  character(len=strLen), save :: feedback_package_file = ''
  character(len=strLen), save :: backend_label = 'WACCMX_STUB'
  character(len=strLen), save :: backend_producer = 'MAGE_WACCMX_STUB'
  character(len=strLen), save :: backend_grid_source = 'REMIX_SM_STUB'
  character(len=strLen), save :: backend_direction = 'MAGE_REMIX_to_future_WACCMX'

  private
  public :: init_waccmx_stub
  public :: init_waccmx_file
  public :: refresh_waccmx_stub_feedback
  public :: refresh_waccmx_file_feedback
  public :: capture_waccmx_stub_exports
  public :: capture_waccmx_file_exports
  public :: write_waccmx_stub_contract
  public :: write_waccmx_file_contract
  public :: write_waccmx_stub_exchange
  public :: write_waccmx_file_exchange
  public :: write_waccmx_stub_package
  public :: write_waccmx_file_package

contains

  subroutine init_waccmx_stub(gcm, ion, sigmaP_floor, sigmaH_floor, sigmaP_oval, sigmaH_oval, feedbackFile, backendName)
    type(gcm_T), intent(inout) :: gcm
    type(mixIon_T), dimension(:), intent(in) :: ion
    real(rp), intent(in) :: sigmaP_floor, sigmaH_floor
    real(rp), intent(in) :: sigmaP_oval, sigmaH_oval
    character(len=*), optional, intent(in) :: feedbackFile
    character(len=*), optional, intent(in) :: backendName

    integer :: h, nH
    real(rp), parameter :: oval_center = 18.0_rp * deg2rad
    real(rp), parameter :: oval_width  = 7.0_rp  * deg2rad
    real(rp), parameter :: neutral_rhs_amp = 2.5e3_rp

    if (present(backendName)) then
      call set_waccmx_backend_labels(trim(backendName))
    else
      call set_waccmx_backend_labels('WACCMX_STUB')
    end if

    nH = min(size(ion), GCMhemispheres)

    gcm%GEO%Coord = 'GEO'
    gcm%APEX%Coord = 'APEX'
    gcm%GEO%gcm2mix_nvar = 1
    gcm%GEO%mix2gcm_nvar = 2
    gcm%APEX%gcm2mix_nvar = 2
    gcm%APEX%mix2gcm_nvar = 2
    gcm%isRestart = .false.
    gcm%nhemi = nH

    gcm%GEO%nlon = ion(1)%G%Np
    gcm%GEO%nhlat = ion(1)%G%Nt
    gcm%APEX%nlon = ion(1)%G%Np
    gcm%APEX%nhlat = ion(1)%G%Nt

    if (.not. allocated(gcm%GEO%inlist)) allocate(gcm%GEO%inlist(gcm%GEO%gcm2mix_nvar))
    if (.not. allocated(gcm%APEX%inlist)) allocate(gcm%APEX%inlist(gcm%APEX%gcm2mix_nvar))
    gcm%GEO%inlist(1) = NEUTRAL_WIND
    gcm%APEX%inlist(1) = SIGMAP
    gcm%APEX%inlist(2) = SIGMAH

    if (.not. allocated(gcm%GEO%outlist)) allocate(gcm%GEO%outlist(gcm%GEO%mix2gcm_nvar))
    if (.not. allocated(gcm%APEX%outlist)) allocate(gcm%APEX%outlist(gcm%APEX%mix2gcm_nvar))
    gcm%GEO%outlist = [AVG_ENG, NUM_FLUX]
    gcm%APEX%outlist = [POT, NUM_FLUX]

    if (.not. allocated(gcm%GEO%mixInput)) allocate(gcm%GEO%mixInput(GCMhemispheres, gcm%GEO%gcm2mix_nvar))
    if (.not. allocated(gcm%APEX%mixInput)) allocate(gcm%APEX%mixInput(GCMhemispheres, gcm%APEX%gcm2mix_nvar))
    if (.not. allocated(gcm%GEO%gcmOutput)) allocate(gcm%GEO%gcmOutput(GCMhemispheres, gcm%GEO%mix2gcm_nvar))
    if (.not. allocated(gcm%APEX%gcmOutput)) allocate(gcm%APEX%gcmOutput(GCMhemispheres, gcm%APEX%mix2gcm_nvar))

    if (present(feedbackFile)) then
      feedback_package_file = trim(feedbackFile)
    else
      feedback_package_file = ''
    end if

    do h = 1, nH
      if (.not. allocated(gcm%GEO%mixInput(h,1)%var)) allocate(gcm%GEO%mixInput(h,1)%var(ion(h)%G%Np, ion(h)%G%Nt))
      if (.not. allocated(gcm%APEX%mixInput(h,1)%var)) allocate(gcm%APEX%mixInput(h,1)%var(ion(h)%G%Np, ion(h)%G%Nt))
      if (.not. allocated(gcm%APEX%mixInput(h,2)%var)) allocate(gcm%APEX%mixInput(h,2)%var(ion(h)%G%Np, ion(h)%G%Nt))

      call fill_stub_neutral_rhs(ion(h)%G%t, ion(h)%G%p, gcm%GEO%mixInput(h,1)%var, &
        neutral_rhs_amp, oval_center, oval_width)
      call fill_stub_conductance(ion(h)%G%t, gcm%APEX%mixInput(h,1)%var, sigmaP_floor, sigmaP_oval, oval_center, oval_width)
      call fill_stub_conductance(ion(h)%G%t, gcm%APEX%mixInput(h,2)%var, sigmaH_floor, sigmaH_oval, oval_center, oval_width)
    end do

    call refresh_waccmx_stub_feedback(gcm, ion)
  end subroutine init_waccmx_stub

  subroutine init_waccmx_file(gcm, ion, sigmaP_floor, sigmaH_floor, sigmaP_oval, sigmaH_oval, feedbackFile)
    type(gcm_T), intent(inout) :: gcm
    type(mixIon_T), dimension(:), intent(in) :: ion
    real(rp), intent(in) :: sigmaP_floor, sigmaH_floor
    real(rp), intent(in) :: sigmaP_oval, sigmaH_oval
    character(len=*), optional, intent(in) :: feedbackFile

    call init_waccmx_stub(gcm, ion, sigmaP_floor, sigmaH_floor, sigmaP_oval, sigmaH_oval, &
      feedbackFile, 'WACCMX_FILE')
  end subroutine init_waccmx_file

  subroutine set_waccmx_backend_labels(name)
    character(len=*), intent(in) :: name

    select case (trim(name))
    case ('WACCMX_FILE')
      backend_label = 'WACCMX_FILE'
      backend_producer = 'MAGE_WACCMX_FILE'
      backend_grid_source = 'REMIX_SM_FILE'
      backend_direction = 'MAGE_REMIX_to_WACCMX'
    case default
      backend_label = 'WACCMX_STUB'
      backend_producer = 'MAGE_WACCMX_STUB'
      backend_grid_source = 'REMIX_SM_STUB'
      backend_direction = 'MAGE_REMIX_to_future_WACCMX'
    end select
  end subroutine set_waccmx_backend_labels

  subroutine refresh_waccmx_stub_feedback(gcm, ion)
    type(gcm_T), intent(inout) :: gcm
    type(mixIon_T), dimension(:), intent(in) :: ion

    type(waccmx_stub_feedback_T) :: feedback
    logical :: fExist

    if (len_trim(feedback_package_file) <= 0) return

    inquire(file=trim(feedback_package_file), exist=fExist)
    if (.not. fExist) return

    call read_waccmx_stub_feedback_package(trim(feedback_package_file), feedback)

    if (size(ion) >= NORTH) call apply_feedback_hemi(gcm, ion(NORTH), NORTH, feedback%north)
    if (size(ion) >= SOUTH) call apply_feedback_hemi(gcm, ion(SOUTH), SOUTH, feedback%south)
  end subroutine refresh_waccmx_stub_feedback

  subroutine refresh_waccmx_file_feedback(gcm, ion)
    type(gcm_T), intent(inout) :: gcm
    type(mixIon_T), dimension(:), intent(in) :: ion

    call refresh_waccmx_stub_feedback(gcm, ion)
  end subroutine refresh_waccmx_file_feedback

  subroutine capture_waccmx_stub_exports(gcm, ion)
    type(gcm_T), intent(inout) :: gcm
    type(mixIon_T), dimension(:), intent(in) :: ion

    integer :: h, nH

    nH = min(size(ion), GCMhemispheres)

    do h = 1, nH
      call copy_field(ion(h)%St%Vars(:,:,AVG_ENG), gcm%GEO%gcmOutput(h,1)%var)
      call copy_field(ion(h)%St%Vars(:,:,NUM_FLUX), gcm%GEO%gcmOutput(h,2)%var)
      call copy_field(ion(h)%St%Vars(:,:,POT),      gcm%APEX%gcmOutput(h,1)%var)
      call copy_field(ion(h)%St%Vars(:,:,NUM_FLUX), gcm%APEX%gcmOutput(h,2)%var)
    end do
  end subroutine capture_waccmx_stub_exports

  subroutine capture_waccmx_file_exports(gcm, ion)
    type(gcm_T), intent(inout) :: gcm
    type(mixIon_T), dimension(:), intent(in) :: ion

    call capture_waccmx_stub_exports(gcm, ion)
  end subroutine capture_waccmx_file_exports

  subroutine fill_stub_conductance(theta, sigma, sigma_floor, sigma_oval, oval_center, oval_width)
    real(rp), intent(in) :: theta(:,:)
    real(rp), intent(out) :: sigma(size(theta,1), size(theta,2))
    real(rp), intent(in) :: sigma_floor, sigma_oval, oval_center, oval_width

    sigma = sigma_floor + sigma_oval * exp(-((theta - oval_center) / oval_width)**2)
  end subroutine fill_stub_conductance

  subroutine fill_stub_neutral_rhs(theta, phi, neutral_rhs, amplitude, oval_center, oval_width)
    real(rp), intent(in) :: theta(:,:), phi(:,:)
    real(rp), intent(out) :: neutral_rhs(size(theta,1), size(theta,2))
    real(rp), intent(in) :: amplitude, oval_center, oval_width

    neutral_rhs = amplitude * exp(-((theta - oval_center) / oval_width)**2) * sin(phi)
  end subroutine fill_stub_neutral_rhs

  subroutine copy_field(src, dst)
    real(rp), intent(in) :: src(:,:)
    real(rp), allocatable, intent(inout) :: dst(:,:)

    if (.not. allocated(dst)) allocate(dst(size(src,1), size(src,2)))
    dst(:,:) = src(:,:)
  end subroutine copy_field

  subroutine apply_feedback_hemi(gcm, ion, h, hemi)
    type(gcm_T), intent(inout) :: gcm
    type(mixIon_T), intent(in) :: ion
    integer, intent(in) :: h
    type(waccmx_feedback_hemi_T), intent(in) :: hemi

    if (.not. allocated(hemi%sigmap)) return
    if (.not. allocated(hemi%sigmah)) return
    if (.not. allocated(hemi%neutral_rhs)) return

    call check_feedback_shape(hemi%sigmap, ion%G%Np, ion%G%Nt, 'sigmap', h)
    call check_feedback_shape(hemi%sigmah, ion%G%Np, ion%G%Nt, 'sigmah', h)
    call check_feedback_shape(hemi%neutral_rhs, ion%G%Np, ion%G%Nt, 'neutral_rhs', h)

    call copy_field(hemi%sigmap, gcm%APEX%mixInput(h,1)%var)
    call copy_field(hemi%sigmah, gcm%APEX%mixInput(h,2)%var)
    call copy_field(hemi%neutral_rhs, gcm%GEO%mixInput(h,1)%var)
  end subroutine apply_feedback_hemi

  subroutine check_feedback_shape(field, np, nt, label, h)
    real(rp), intent(in) :: field(:,:)
    integer, intent(in) :: np, nt, h
    character(len=*), intent(in) :: label

    if (size(field,1) /= np .or. size(field,2) /= nt) then
      write(*,*) 'WACCMX feedback shape mismatch for hemisphere ', h, ' field ', trim(label)
      write(*,*) 'Expected ', np, ' x ', nt, ' but got ', size(field,1), ' x ', size(field,2)
      stop
    end if
  end subroutine check_feedback_shape

  subroutine write_waccmx_stub_contract(path, gcm)
    character(len=*), intent(in) :: path
    type(gcm_T), intent(in) :: gcm

    integer :: unitno, h

    open(newunit=unitno, file=trim(path), status='replace', action='write')
    write(unitno,'(a)') '# ' // trim(backend_label) // ' contract summary'
    if (trim(backend_label) == 'WACCMX_FILE') then
      write(unitno,'(a)') '# Purpose: formal WACCM-X file-coupling backend for non-MPI voltron.x.'
    else
      write(unitno,'(a)') '# Purpose: wire WACCM-X style file coupling into stock non-MPI voltron.x.'
    end if
    write(unitno,'(a)') ''
    write(unitno,'(a)') 'MAGE -> WACCM-X fields:'
    write(unitno,'(a)') '  POT'
    write(unitno,'(a)') '  AVG_ENG'
    write(unitno,'(a)') '  NUM_FLUX'
    write(unitno,'(a)') ''
    write(unitno,'(a)') 'WACCM-X -> MAGE/REMIX fields:'
    write(unitno,'(a)') '  SIGMAP'
    write(unitno,'(a)') '  SIGMAH'
    write(unitno,'(a)') '  NEUTRAL_DYNAMO_RHS (mapped to NEUTRAL_WIND slot)'
    write(unitno,'(a)') ''
    if (len_trim(feedback_package_file) > 0) then
      write(unitno,'(a,a)') 'External feedback package (optional): ', trim(feedback_package_file)
      write(unitno,'(a)') ''
    end if
    do h = 1, GCMhemispheres
      if (.not. allocated(gcm%APEX%mixInput(h,1)%var)) cycle
      write(unitno,'(a,i0)') 'Hemisphere ', h
      write(unitno,'(a,2(i0,a))') '  Grid: ', size(gcm%APEX%mixInput(h,1)%var,1), ' x ', size(gcm%APEX%mixInput(h,1)%var,2)
      write(unitno,'(a,2(f8.3,a))') '  SIGMAP min/max: ', minval(gcm%APEX%mixInput(h,1)%var), ' / ', maxval(gcm%APEX%mixInput(h,1)%var), ' S'
      write(unitno,'(a,2(f8.3,a))') '  SIGMAH min/max: ', minval(gcm%APEX%mixInput(h,2)%var), ' / ', maxval(gcm%APEX%mixInput(h,2)%var), ' S'
      if (allocated(gcm%GEO%mixInput(h,1)%var)) then
        write(unitno,'(a,f10.3,a)') '  NEUTRAL_DYNAMO_RHS absmax: ', maxval(abs(gcm%GEO%mixInput(h,1)%var)), ' cm/s'
      end if
    end do
    close(unitno)
  end subroutine write_waccmx_stub_contract

  subroutine write_waccmx_file_contract(path, gcm)
    character(len=*), intent(in) :: path
    type(gcm_T), intent(in) :: gcm

    call write_waccmx_stub_contract(path, gcm)
  end subroutine write_waccmx_file_contract

  subroutine write_waccmx_stub_exchange(path, gcm)
    character(len=*), intent(in) :: path
    type(gcm_T), intent(in) :: gcm

    integer :: unitno, h, v

    open(newunit=unitno, file=trim(path), status='replace', action='write')
    write(unitno,'(a)') '# ' // trim(backend_label) // ' forward exchange summary'
    write(unitno,'(a)') '# Direction: MAGE/REMIX -> WACCM-X'
    write(unitno,'(a)') ''
    write(unitno,'(a)') '| Coord | Field | Units | Hemisphere | Grid | Min | Max |'
    write(unitno,'(a)') '| --- | --- | --- | --- | --- | ---: | ---: |'

    do h = 1, GCMhemispheres
      do v = 1, gcm%GEO%mix2gcm_nvar
        if (.not. allocated(gcm%GEO%gcmOutput(h,v)%var)) cycle
        call write_field_row(unitno, gcm%GEO%Coord, gcm%GEO%outlist(v), h, gcm%GEO%gcmOutput(h,v)%var)
      end do
      do v = 1, gcm%APEX%mix2gcm_nvar
        if (.not. allocated(gcm%APEX%gcmOutput(h,v)%var)) cycle
        call write_field_row(unitno, gcm%APEX%Coord, gcm%APEX%outlist(v), h, gcm%APEX%gcmOutput(h,v)%var)
      end do
    end do
    close(unitno)
  end subroutine write_waccmx_stub_exchange

  subroutine write_waccmx_file_exchange(path, gcm)
    character(len=*), intent(in) :: path
    type(gcm_T), intent(in) :: gcm

    call write_waccmx_stub_exchange(path, gcm)
  end subroutine write_waccmx_file_exchange

  subroutine write_waccmx_stub_package(path, gcm, ion, mjd, time, source_mix)
    character(len=*), intent(in) :: path, source_mix
    type(gcm_T), intent(in) :: gcm
    type(mixIon_T), dimension(:), intent(in) :: ion
    real(rp), intent(in) :: mjd, time

    type(IOVAR_T), dimension(MAXIOVAR) :: IOVars
    integer :: h

    call ClearIO(IOVars)
    call AddOutVar(IOVars, "schema_version", "0.1")
    call AddOutVar(IOVars, "producer", trim(backend_producer))
    call AddOutVar(IOVars, "grid_source", trim(backend_grid_source))
    call AddOutVar(IOVars, "direction", trim(backend_direction))
    call AddOutVar(IOVars, "source_mix", trim(source_mix))
    call AddOutVar(IOVars, "time_seconds", time, uStr="s", dStr="Source MIX time")
    call AddOutVar(IOVars, "mjd", mjd, uStr="days", dStr="Source MIX modified Julian date")
    call WriteVars(IOVars, .false., path, gStrO="/Meta")

    do h = 1, min(size(ion), GCMhemispheres)
      call write_grid_group(path, trim(hemisphere_name(h)), ion(h))
      call write_export_group(path, trim(hemisphere_name(h)) // "_GEO", "GEO", trim(backend_grid_source), &
        ion(h)%G%t, ion(h)%G%p, gcm%GEO%gcmOutput(h,1)%var, gcm%GEO%gcmOutput(h,2)%var, &
        "AVG_ENG", "NUM_FLUX", "keV", "1/cm^2 s")
      call write_export_group(path, trim(hemisphere_name(h)) // "_APEX", "APEX", trim(backend_grid_source), &
        ion(h)%G%t, ion(h)%G%p, gcm%APEX%gcmOutput(h,1)%var, gcm%APEX%gcmOutput(h,2)%var, &
        "POT", "NUM_FLUX", "kV", "1/cm^2 s")
    end do
    call write_waccmx_sami3_phi_payload_if_enabled(gcm, ion, time)
  end subroutine write_waccmx_stub_package

  subroutine write_waccmx_sami3_phi_payload_if_enabled(gcm, ion, time)
    type(gcm_T), intent(in) :: gcm
    type(mixIon_T), dimension(:), intent(in) :: ion
    real(rp), intent(in) :: time

    character(len=strLen) :: payload_file, grid_file, hemi_env, value
    integer :: stat, lenval, hemi, ios
    real(rp) :: frame_hour, valid_until
    real(rp) :: target_mlat(sami3_phi_nlat), target_mlon(sami3_phi_nlon)
    real(real32) :: phi_statv(sami3_phi_nlat, sami3_phi_nlon)

    payload_file = ''
    call get_environment_variable('WACCMX_SAMI3_PHI_PAYLOAD_FILE', payload_file, &
      length=lenval, status=stat)
    if (stat /= 0 .or. len_trim(payload_file) <= 0) return

    grid_file = ''
    call get_environment_variable('WACCMX_SAMI3_WEIMER_GRID', grid_file, &
      length=lenval, status=stat)
    if (stat /= 0 .or. len_trim(grid_file) <= 0) then
      write(*,*) 'WACCMX_SAMI3_PHI_PAYLOAD_FILE is set but WACCMX_SAMI3_WEIMER_GRID is missing.'
      stop
    end if

    hemi = NORTH
    hemi_env = ''
    call get_environment_variable('WACCMX_SAMI3_PHI_HEMI', hemi_env, &
      length=lenval, status=stat)
    if (stat == 0) then
      select case (trim(hemi_env))
      case ('SOUTH', 'south', '2')
        hemi = SOUTH
      case default
        hemi = NORTH
      end select
    end if
    if (size(ion) < hemi) then
      write(*,*) 'Requested WACCMX_SAMI3_PHI_HEMI is unavailable: ', hemi
      stop
    end if
    if (.not. allocated(gcm%APEX%gcmOutput)) then
      stop 'WACCMX_SAMI3_PHI_PAYLOAD requested before APEX GCM output allocation.'
    end if
    if (.not. allocated(gcm%APEX%gcmOutput(hemi,1)%var)) then
      stop 'WACCMX_SAMI3_PHI_PAYLOAD requested before APEX POT capture.'
    end if

    frame_hour = time/3600.0_rp
    value = ''
    call get_environment_variable('WACCMX_SAMI3_PHI_FRAME_HOUR', value, &
      length=lenval, status=stat)
    if (stat == 0 .and. len_trim(value) > 0) read(value,*,iostat=ios) frame_hour

    valid_until = 1.0e30_rp
    value = ''
    call get_environment_variable('WACCMX_SAMI3_PHI_VALID_UNTIL_HOUR', value, &
      length=lenval, status=stat)
    if (stat == 0 .and. len_trim(value) > 0) read(value,*,iostat=ios) valid_until

    call read_sami3_weimer_grid(trim(grid_file), target_mlat, target_mlon)
    call remix_pot_to_sami3_phi(ion(hemi)%G%t, ion(hemi)%G%p, &
      gcm%APEX%gcmOutput(hemi,1)%var, target_mlat, target_mlon, phi_statv)
    call write_sami3_phi_payload(trim(payload_file), phi_statv, frame_hour, valid_until)

    write(*,*) 'WACCMX_SAMI3_PHI_PAYLOAD wrote ', trim(payload_file), &
      ' hemi=', hemi, ' hour=', frame_hour, ' valid_until=', valid_until, &
      ' source_min/max=', minval(gcm%APEX%gcmOutput(hemi,1)%var), &
      maxval(gcm%APEX%gcmOutput(hemi,1)%var), &
      ' payload_min/max=', minval(phi_statv), maxval(phi_statv)
  end subroutine write_waccmx_sami3_phi_payload_if_enabled

  subroutine read_sami3_weimer_grid(path, target_mlat, target_mlon)
    character(len=*), intent(in) :: path
    real(rp), intent(out) :: target_mlat(:), target_mlon(:)

    integer :: unitno, ios

    open(newunit=unitno, file=trim(path), status='old', action='read', iostat=ios)
    if (ios /= 0) then
      write(*,*) 'Unable to open SAMI3 Weimer grid file: ', trim(path), ' iostat=', ios
      stop
    end if

    read(unitno,*,iostat=ios) target_mlat, target_mlon
    if (ios /= 0) stop 'Failed reading SAMI3 Weimer grid.'
    close(unitno)
  end subroutine read_sami3_weimer_grid

  subroutine remix_pot_to_sami3_phi(theta, phi, pot_kv, target_mlat, target_mlon, phi_statv)
    real(rp), intent(in) :: theta(:,:), phi(:,:), pot_kv(:,:)
    real(rp), intent(in) :: target_mlat(:), target_mlon(:)
    real(real32), intent(out) :: phi_statv(size(target_mlat), size(target_mlon))

    integer :: nsrc_lat, nsrc_lon, i, j
    real(rp), allocatable :: source_mlat(:), source_mlon(:)
    real(rp), allocatable :: pot_lat_lon(:,:), lon_interp(:,:)
    real(rp) :: value_kv

    nsrc_lon = size(pot_kv, 1)
    nsrc_lat = size(pot_kv, 2)
    if (size(theta,1) /= nsrc_lon .or. size(theta,2) /= nsrc_lat .or. &
        size(phi,1) /= nsrc_lon .or. size(phi,2) /= nsrc_lat) then
      stop 'REMIX theta/phi/POT shape mismatch for SAMI3 phi payload.'
    end if

    allocate(source_mlat(nsrc_lat), source_mlon(nsrc_lon))
    allocate(pot_lat_lon(nsrc_lat, nsrc_lon))
    allocate(lon_interp(nsrc_lat, size(target_mlon)))

    do i = 1, nsrc_lat
      source_mlat(i) = 90.0_rp - theta(1,i)*rad2deg
    end do
    do j = 1, nsrc_lon
      source_mlon(j) = modulo(phi(j,1)*rad2deg, 360.0_rp)
    end do
    do i = 1, nsrc_lat
      do j = 1, nsrc_lon
        pot_lat_lon(i,j) = pot_kv(j,i)
      end do
    end do

    call interp_periodic_lon(source_mlon, pot_lat_lon, target_mlon, lon_interp)

    do i = 1, size(target_mlat)
      do j = 1, size(target_mlon)
        value_kv = interp_descending_lat(source_mlat, lon_interp(:,j), target_mlat(i))
        phi_statv(i,j) = real(value_kv*statvolt_per_kv, real32)
      end do
    end do

    if (.not. all(ieee_is_finite(phi_statv))) then
      stop 'Non-finite SAMI3 phi payload value generated from REMIX POT.'
    end if

    deallocate(source_mlat, source_mlon, pot_lat_lon, lon_interp)
  end subroutine remix_pot_to_sami3_phi

  subroutine interp_periodic_lon(source_mlon, field, target_mlon, out)
    real(rp), intent(in) :: source_mlon(:), field(:,:), target_mlon(:)
    real(rp), intent(out) :: out(size(field,1), size(target_mlon))

    integer :: i, j, jl, jr, nlon
    real(rp) :: lonq, lonl, lonr, frac

    nlon = size(source_mlon)
    do i = 1, size(field,1)
      do j = 1, size(target_mlon)
        lonq = modulo(target_mlon(j), 360.0_rp)
        if (lonq <= source_mlon(nlon)) then
          jl = 1
          jr = 1
          do jr = 2, nlon
            if (lonq <= source_mlon(jr)) then
              jl = jr - 1
              exit
            end if
          end do
          lonl = source_mlon(jl)
          lonr = source_mlon(jr)
        else
          jl = nlon
          jr = 1
          lonl = source_mlon(nlon)
          lonr = source_mlon(1) + 360.0_rp
        end if
        if (lonr == lonl) then
          out(i,j) = field(i,jl)
        else
          frac = (lonq - lonl)/(lonr - lonl)
          out(i,j) = (1.0_rp - frac)*field(i,jl) + frac*field(i,jr)
        end if
      end do
    end do
  end subroutine interp_periodic_lon

  function interp_descending_lat(source_mlat, field_lat, target_mlat) result(value)
    real(rp), intent(in) :: source_mlat(:), field_lat(:), target_mlat
    real(rp) :: value

    integer :: i
    real(rp) :: frac

    if (target_mlat < minval(source_mlat)) then
      value = 0.0_rp
      return
    end if
    if (target_mlat >= source_mlat(1)) then
      value = field_lat(1)
      return
    end if

    do i = 1, size(source_mlat) - 1
      if (target_mlat <= source_mlat(i) .and. target_mlat >= source_mlat(i+1)) then
        frac = (source_mlat(i) - target_mlat)/(source_mlat(i) - source_mlat(i+1))
        value = (1.0_rp - frac)*field_lat(i) + frac*field_lat(i+1)
        return
      end if
    end do

    value = field_lat(size(field_lat))
  end function interp_descending_lat

  subroutine write_sami3_phi_payload(path, phi_statv, frame_hour, valid_until)
    character(len=*), intent(in) :: path
    real(real32), intent(in) :: phi_statv(:,:)
    real(rp), intent(in) :: frame_hour, valid_until

    integer :: unitno
    integer(int32) :: header(5), frame_index
    real(real32) :: frame_meta(2)

    header = [sami3_phi_magic, sami3_phi_version, int(size(phi_statv,1), int32), &
      int(size(phi_statv,2), int32), 1_int32]
    frame_index = 0_int32
    frame_meta = [real(frame_hour, real32), real(valid_until, real32)]

    open(newunit=unitno, file=trim(path), form='unformatted', access='stream', &
      status='replace', action='write')
    write(unitno) header
    write(unitno) frame_index
    write(unitno) frame_meta
    write(unitno) phi_statv
    close(unitno)
  end subroutine write_sami3_phi_payload

  subroutine write_waccmx_file_package(path, gcm, ion, mjd, time, source_mix)
    character(len=*), intent(in) :: path, source_mix
    type(gcm_T), intent(in) :: gcm
    type(mixIon_T), dimension(:), intent(in) :: ion
    real(rp), intent(in) :: mjd, time

    call write_waccmx_stub_package(path, gcm, ion, mjd, time, source_mix)
  end subroutine write_waccmx_file_package

  subroutine write_grid_group(path, hemi_name, ion)
    character(len=*), intent(in) :: path, hemi_name
    type(mixIon_T), intent(in) :: ion

    type(IOVAR_T), dimension(MAXIOVAR) :: IOVars

    call ClearIO(IOVars)
    call AddOutVar(IOVars, "hemisphere", trim(hemi_name))
    call AddOutVar(IOVars, "coord", "SM")
    call AddOutVar(IOVars, "theta", ion%G%t, uStr="rad", dStr="REMIX shell-grid colatitude")
    call AddOutVar(IOVars, "phi", ion%G%p, uStr="rad", dStr="REMIX shell-grid longitude")
    call AddOutVar(IOVars, "theta_deg", ion%G%t * rad2deg, uStr="deg", dStr="REMIX shell-grid colatitude")
    call AddOutVar(IOVars, "phi_deg", ion%G%p * rad2deg, uStr="deg", dStr="REMIX shell-grid longitude")
    call WriteVars(IOVars, .false., path, gStrO="/" // trim(hemi_name) // "_GRID")
  end subroutine write_grid_group

  subroutine write_export_group(path, group_name, coord_name, grid_source, theta, phi, field1, field2, field1_name, field2_name, field1_units, field2_units)
    character(len=*), intent(in) :: path, group_name, coord_name, grid_source
    character(len=*), intent(in) :: field1_name, field2_name, field1_units, field2_units
    real(rp), intent(in) :: theta(:,:), phi(:,:), field1(:,:), field2(:,:)

    type(IOVAR_T), dimension(MAXIOVAR) :: IOVars

    call ClearIO(IOVars)
    call AddOutVar(IOVars, "coord", trim(coord_name))
    call AddOutVar(IOVars, "grid_source", trim(grid_source))
    call AddOutVar(IOVars, "theta", theta, uStr="rad", dStr="Prototype export grid colatitude")
    call AddOutVar(IOVars, "phi", phi, uStr="rad", dStr="Prototype export grid longitude")
    call AddOutVar(IOVars, trim(field1_name), field1, uStr=trim(field1_units), dStr="Forward exchange field")
    call AddOutVar(IOVars, trim(field2_name), field2, uStr=trim(field2_units), dStr="Forward exchange field")
    call WriteVars(IOVars, .false., path, gStrO="/" // trim(group_name))
  end subroutine write_export_group

  subroutine write_field_row(unitno, coord, field_id, hemisphere, field)
    integer, intent(in) :: unitno, field_id, hemisphere
    character(len=*), intent(in) :: coord
    real(rp), intent(in) :: field(:,:)
    character(len=strLen) :: grid_str

    write(grid_str,'(i0,a,i0)') size(field,1), 'x', size(field,2)
    write(unitno,'(a)') '| ' // trim(coord) // ' | ' // trim(field_name(field_id)) // ' | ' // &
      trim(field_units(field_id)) // ' | ' // trim(hemisphere_name(hemisphere)) // ' | ' // trim(grid_str) // &
      ' | ' // trim(real_to_str(minval(field))) // ' | ' // trim(real_to_str(maxval(field))) // ' |'
  end subroutine write_field_row

  function field_name(field_id) result(name)
    integer, intent(in) :: field_id
    character(len=strLen) :: name

    select case (field_id)
    case (POT)
      name = 'POT'
    case (AVG_ENG)
      name = 'AVG_ENG'
    case (NUM_FLUX)
      name = 'NUM_FLUX'
    case (SIGMAP)
      name = 'SIGMAP'
    case (SIGMAH)
      name = 'SIGMAH'
    case default
      write(name,'(a,i0)') 'FIELD_', field_id
    end select
  end function field_name

  function field_units(field_id) result(units)
    integer, intent(in) :: field_id
    character(len=strLen) :: units

    select case (field_id)
    case (POT)
      units = 'kV'
    case (AVG_ENG)
      units = 'keV'
    case (NUM_FLUX)
      units = '1/cm^2 s'
    case (SIGMAP, SIGMAH)
      units = 'S'
    case default
      units = 'unknown'
    end select
  end function field_units

  function hemisphere_name(hemisphere) result(name)
    integer, intent(in) :: hemisphere
    character(len=strLen) :: name

    select case (hemisphere)
    case (NORTH)
      name = 'NORTH'
    case (SOUTH)
      name = 'SOUTH'
    case default
      write(name,'(a,i0)') 'HEMI_', hemisphere
    end select
  end function hemisphere_name

  function real_to_str(value) result(text)
    real(rp), intent(in) :: value
    character(len=strLen) :: text

    write(text,'(es12.5)') value
  end function real_to_str

end module waccmx_stub_backend
