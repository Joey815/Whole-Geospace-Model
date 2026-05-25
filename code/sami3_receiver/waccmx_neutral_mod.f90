module waccmx_neutral_mod

    use parameter_mod
    use namelist_mod
    use message_passing_mod
    use variable_mod
    use grid_mod, only: alts

    implicit none

    integer, parameter :: waccmx_magic = 20260522
    integer, parameter :: waccmx_tag_header = 200
    integer, parameter :: waccmx_tag_hr = 201
    integer, parameter :: waccmx_tag_denni = 202
    integer, parameter :: waccmx_tag_tni = 203
    integer, parameter :: waccmx_tag_ui = 204
    integer, parameter :: waccmx_tag_vi = 205
    integer, parameter :: waccmx_tag_wi = 206
    integer, parameter :: waccmx_tag_dennf = 207
    integer, parameter :: waccmx_tag_tnf = 208
    integer, parameter :: waccmx_tag_uf = 209
    integer, parameter :: waccmx_tag_vf = 210
    integer, parameter :: waccmx_tag_wf = 211
    integer, parameter :: waccmx_tag_source_flags = 212
    integer, parameter :: waccmx_phi_magic = 20260524
    integer, parameter :: waccmx_tag_phi_header = 220
    integer, parameter :: waccmx_tag_phi_hour = 221
    integer, parameter :: waccmx_tag_phi_valid_until = 222
    integer, parameter :: waccmx_tag_phi_data = 223
    integer, parameter :: waccmx_tag_done = 299
    integer, parameter :: waccmx_flag_valid = 1
    integer, parameter :: waccmx_flag_above_top = 2
    integer, parameter :: waccmx_flag_n2_invalid = 3
    integer, parameter :: waccmx_flag_other_invalid = 4

    logical :: waccmx_loaded = .false.
    logical :: waccmx_online_connected = .false.
    logical :: waccmx_apply_policy_logged = .false.
    logical :: waccmx_top_blend_initialized = .false.
    logical :: waccmx_top_blend_enabled = .false.
    logical :: waccmx_neutral_timing_initialized = .false.
    real :: waccmx_top_blend_bottom_km = 0.0
    real :: waccmx_top_blend_top_km = 0.0
    real :: waccmx_neutral_update_hours_value = 0.25
    real :: waccmx_neutral_span_hours_value = 0.25
    integer :: waccmx_peer_comm = -1
    integer :: waccmx_phi_peer_comm = -1
    integer :: waccmx_online_packet_count = 0
    integer :: waccmx_online_done_value = -1
    real :: waccmx_loaded_request_hr = -1.0e30
    logical :: waccmx_online_done_received = .false.
    character(len=256) :: waccmx_online_port_name = ''
    character(len=256) :: waccmx_phi_direct_port_name = ''
    character(len=512) :: waccmx_phi_direct_port_file = ''
    logical :: waccmx_phi_direct_connected = .false.
    logical :: waccmx_phi_direct_final_seen = .false.

    real, allocatable :: w_denni(:,:,:,:), w_dennf(:,:,:,:)
    real, allocatable :: w_tni(:,:,:), w_tnf(:,:,:)
    real, allocatable :: w_ui(:,:,:), w_uf(:,:,:)
    real, allocatable :: w_vi(:,:,:), w_vf(:,:,:)
    real, allocatable :: w_wi(:,:,:), w_wf(:,:,:)
    integer, allocatable :: w_source_flag(:,:,:)

contains

    subroutine waccmx_alloc_arrays()

        if (.not. allocated(w_denni)) then
            allocate(w_denni(nz,nf,nl,nneut), w_dennf(nz,nf,nl,nneut))
            allocate(w_tni(nz,nf,nl), w_tnf(nz,nf,nl))
            allocate(w_ui(nz,nf,nl), w_uf(nz,nf,nl))
            allocate(w_vi(nz,nf,nl), w_vf(nz,nf,nl))
            allocate(w_wi(nz,nf,nl), w_wf(nz,nf,nl))
            allocate(w_source_flag(nz,nf,nl))
        endif

    end subroutine waccmx_alloc_arrays

    logical function waccmx_recv_qc_enabled()

        integer :: stat, lenval
        character(len=32) :: value

        value = ''
        call get_environment_variable('WXSAMI3_RECV_QC', value, length=lenval, status=stat)
        waccmx_recv_qc_enabled = .false.
        if (stat == 0 .and. lenval > 0) then
            if (trim(value) /= '0' .and. trim(value) /= 'false' .and. &
                trim(value) /= 'FALSE') then
                waccmx_recv_qc_enabled = .true.
            endif
        endif

    end function waccmx_recv_qc_enabled

    logical function waccmx_online_phi_enabled()

        integer :: stat, lenval
        character(len=32) :: value

        value = ''
        call get_environment_variable('SAMI3_USE_ONLINE_PHI_WEIMER', value, &
                                      length=lenval, status=stat)
        waccmx_online_phi_enabled = .false.
        if (stat == 0 .and. lenval > 0) then
            if (trim(value) == '1' .or. trim(value) == 'true' .or. &
                trim(value) == 'TRUE') then
                waccmx_online_phi_enabled = .true.
            endif
        endif

    end function waccmx_online_phi_enabled

    logical function waccmx_phi_direct_enabled()

        integer :: stat, lenval

        waccmx_phi_direct_port_file = ''
        call get_environment_variable('SAMI3_PHI_DIRECT_PORT_FILE', &
                                      waccmx_phi_direct_port_file, &
                                      length=lenval, status=stat)
        waccmx_phi_direct_enabled = stat == 0 .and. lenval > 0
        if (waccmx_phi_direct_enabled) then
            waccmx_phi_direct_port_file = adjustl(waccmx_phi_direct_port_file)
        endif

    end function waccmx_phi_direct_enabled

    logical function waccmx_phi_skip_madala_after_final_enabled()

        integer :: stat, lenval
        character(len=32) :: value

        value = ''
        call get_environment_variable('SAMI3_PHI_SKIP_MADALA_AFTER_FINAL', &
                                      value, length=lenval, status=stat)
        waccmx_phi_skip_madala_after_final_enabled = .false.
        if (stat == 0 .and. lenval > 0) then
            if (trim(value) == '1' .or. trim(value) == 'true' .or. &
                trim(value) == 'TRUE') then
                waccmx_phi_skip_madala_after_final_enabled = .true.
            endif
        endif

    end function waccmx_phi_skip_madala_after_final_enabled

    logical function waccmx_phi_final_frame_seen()

        waccmx_phi_final_frame_seen = waccmx_phi_direct_final_seen

    end function waccmx_phi_final_frame_seen

    subroutine waccmx_init_neutral_timing_policy()

        integer :: stat, lenval, ios
        character(len=64) :: value

        if (waccmx_neutral_timing_initialized) return

        waccmx_neutral_update_hours_value = 0.25
        value = ''
        call get_environment_variable('WXSAMI3_NEUTRAL_UPDATE_HOURS', &
                                      value, length=lenval, status=stat)
        if (stat == 0 .and. lenval > 0) then
            read(value,*,iostat=ios) waccmx_neutral_update_hours_value
            if (ios /= 0 .or. waccmx_neutral_update_hours_value <= 0.0) then
                print *, 'WACCMX neutral timing invalid WXSAMI3_NEUTRAL_UPDATE_HOURS=', &
                         trim(value)
                stop
            endif
        endif

        waccmx_neutral_span_hours_value = waccmx_neutral_update_hours_value
        value = ''
        call get_environment_variable('WXSAMI3_NEUTRAL_SPAN_HOURS', &
                                      value, length=lenval, status=stat)
        if (stat == 0 .and. lenval > 0) then
            read(value,*,iostat=ios) waccmx_neutral_span_hours_value
            if (ios /= 0 .or. waccmx_neutral_span_hours_value <= 0.0) then
                print *, 'WACCMX neutral timing invalid WXSAMI3_NEUTRAL_SPAN_HOURS=', &
                         trim(value)
                stop
            endif
        endif

        if (taskid == 1 .and. lwaccmx_neutral) then
            print *, 'WACCMX neutral timing policy: update_hours,span_hours=', &
                     waccmx_neutral_update_hours_value, &
                     waccmx_neutral_span_hours_value
        endif

        waccmx_neutral_timing_initialized = .true.

    end subroutine waccmx_init_neutral_timing_policy

    real function waccmx_neutral_update_hours()

        call waccmx_init_neutral_timing_policy()
        waccmx_neutral_update_hours = waccmx_neutral_update_hours_value

    end function waccmx_neutral_update_hours

    real function waccmx_neutral_span_hours()

        call waccmx_init_neutral_timing_policy()
        waccmx_neutral_span_hours = waccmx_neutral_span_hours_value

    end function waccmx_neutral_span_hours

    subroutine waccmx_phi_direct_init()

        include 'mpif.h'

        integer :: ierr, unit, ios
        character(len=MPI_MAX_PORT_NAME) :: port_name

        if (taskid /= 0) return
        if (waccmx_phi_direct_connected) return
        if (.not. waccmx_phi_direct_enabled()) return

        port_name = ''
        call MPI_Open_port(MPI_INFO_NULL, port_name, ierr)
        if (ierr /= MPI_SUCCESS) then
            print *, 'SAMI3 direct phi MPI_Open_port failed ierr=', ierr
            call MPI_Abort(sami3_comm, ierr, ierr)
        endif
        waccmx_phi_direct_port_name = port_name
        open(newunit=unit, file=trim(waccmx_phi_direct_port_file), &
             status='replace', action='write', iostat=ios)
        if (ios /= 0) then
            print *, 'SAMI3 direct phi port file open failed: ', &
                     trim(waccmx_phi_direct_port_file), ios
            call MPI_Abort(sami3_comm, ios, ierr)
        endif
        write(unit,'(A)') trim(port_name)
        close(unit)
        print *, 'SAMI3 direct phi port ready: ', trim(waccmx_phi_direct_port_file)

        call MPI_Comm_accept(port_name, MPI_INFO_NULL, 0, MPI_COMM_SELF, &
                             waccmx_phi_peer_comm, ierr)
        if (ierr /= MPI_SUCCESS) then
            print *, 'SAMI3 direct phi MPI_Comm_accept failed ierr=', ierr
            call MPI_Abort(sami3_comm, ierr, ierr)
        endif
        waccmx_phi_direct_connected = .true.
        print *, 'SAMI3 direct phi sender connected'

    end subroutine waccmx_phi_direct_init

    subroutine waccmx_phi_direct_finalize()

        include 'mpif.h'

        integer :: ierr
        integer :: done_value

        if (taskid /= 0) return
        if (.not. waccmx_phi_direct_connected) return

        call MPI_Recv(done_value, 1, MPI_INTEGER, 0, waccmx_tag_done, &
                      waccmx_phi_peer_comm, MPI_STATUS_IGNORE, ierr)
        if (ierr /= MPI_SUCCESS) then
            print *, 'SAMI3 direct phi done receive failed ierr=', ierr
            call MPI_Abort(sami3_comm, ierr, ierr)
        endif
        print *, 'SAMI3 direct phi done signal received:', done_value

        call MPI_Comm_disconnect(waccmx_phi_peer_comm, ierr)
        if (len_trim(waccmx_phi_direct_port_name) > 0) then
            call MPI_Close_port(waccmx_phi_direct_port_name, ierr)
        endif
        waccmx_phi_direct_connected = .false.

    end subroutine waccmx_phi_direct_finalize

    subroutine waccmx_recv_phi_weimer_online(phi_weimer_real, hrut, hrutw2)

        include 'mpif.h'

        real, intent(out) :: phi_weimer_real(nfp1,nlt+1)
        real, intent(in) :: hrut
        real, intent(out) :: hrutw2
        integer :: ierr
        integer :: header(6)
        integer :: nphi
        integer :: phi_comm
        real :: frame_hour
        logical :: use_direct_phi

        if (.not. waccmx_online_phi_enabled()) return
        if (taskid /= 0) return
        use_direct_phi = waccmx_phi_direct_enabled()
        if (use_direct_phi) then
            call waccmx_phi_direct_init()
            phi_comm = waccmx_phi_peer_comm
        else if (waccmx_online_connected) then
            phi_comm = waccmx_peer_comm
        else
            print *, 'WACCMX online phi receive requested before connection'
            call MPI_Abort(sami3_comm, 9201, ierr)
        endif

        nphi = nfp1*(nlt+1)

        call MPI_Recv(header, 6, MPI_INTEGER, 0, waccmx_tag_phi_header, &
                      phi_comm, MPI_STATUS_IGNORE, ierr)
        if (ierr /= MPI_SUCCESS) then
            print *, 'WACCMX online phi header receive failed ierr=', ierr
            call MPI_Abort(sami3_comm, ierr, ierr)
        endif
        if (header(1) /= waccmx_phi_magic .or. header(2) /= 1 .or. &
            header(3) /= nfp1 .or. header(4) /= nlt+1) then
            print *, 'WACCMX online phi header mismatch'
            print *, 'header=', header
            print *, 'expected=', waccmx_phi_magic, 1, nfp1, nlt+1
            call MPI_Abort(sami3_comm, 9202, ierr)
        endif

        call MPI_Recv(frame_hour, 1, MPI_REAL, 0, waccmx_tag_phi_hour, &
                      phi_comm, MPI_STATUS_IGNORE, ierr)
        call MPI_Recv(hrutw2, 1, MPI_REAL, 0, waccmx_tag_phi_valid_until, &
                      phi_comm, MPI_STATUS_IGNORE, ierr)
        call MPI_Recv(phi_weimer_real, nphi, MPI_REAL, 0, waccmx_tag_phi_data, &
                      phi_comm, MPI_STATUS_IGNORE, ierr)
        if (header(5) + 1 >= header(6)) waccmx_phi_direct_final_seen = .true.

        print *, 'WACCMX_PHI_RECV', header(5), header(6), hrut, frame_hour, &
                 hrutw2, minval(phi_weimer_real), maxval(phi_weimer_real)

    end subroutine waccmx_recv_phi_weimer_online

    subroutine waccmx_init_top_blend_policy()

        integer :: stat, lenval, ios
        character(len=32) :: mode
        character(len=64) :: value

        if (waccmx_top_blend_initialized) return

        mode = ''
        call get_environment_variable('WXSAMI3_TOP_BLEND_MODE', mode, &
                                      length=lenval, status=stat)
        if (stat == 0 .and. lenval > 0) then
            if (trim(mode) == 'linear' .or. trim(mode) == 'LINEAR') then
                waccmx_top_blend_enabled = .true.
            else if (trim(mode) == 'none' .or. trim(mode) == 'NONE' .or. &
                     trim(mode) == '0' .or. trim(mode) == 'false' .or. &
                     trim(mode) == 'FALSE') then
                waccmx_top_blend_enabled = .false.
            else
                print *, 'WACCMX top blend invalid WXSAMI3_TOP_BLEND_MODE=', &
                         trim(mode)
                stop
            endif
        endif

        if (waccmx_top_blend_enabled) then
            value = ''
            call get_environment_variable('WXSAMI3_BLEND_BOTTOM_KM', value, &
                                          length=lenval, status=stat)
            if (stat /= 0 .or. lenval <= 0) then
                print *, 'WACCMX top blend requires WXSAMI3_BLEND_BOTTOM_KM'
                stop
            endif
            read(value,*,iostat=ios) waccmx_top_blend_bottom_km
            if (ios /= 0) then
                print *, 'WACCMX top blend could not parse WXSAMI3_BLEND_BOTTOM_KM=', &
                         trim(value)
                stop
            endif

            value = ''
            call get_environment_variable('WXSAMI3_BLEND_TOP_KM', value, &
                                          length=lenval, status=stat)
            if (stat /= 0 .or. lenval <= 0) then
                print *, 'WACCMX top blend requires WXSAMI3_BLEND_TOP_KM'
                stop
            endif
            read(value,*,iostat=ios) waccmx_top_blend_top_km
            if (ios /= 0) then
                print *, 'WACCMX top blend could not parse WXSAMI3_BLEND_TOP_KM=', &
                         trim(value)
                stop
            endif

            if (waccmx_top_blend_top_km <= waccmx_top_blend_bottom_km) then
                print *, 'WACCMX top blend requires top_km > bottom_km', &
                         waccmx_top_blend_bottom_km, waccmx_top_blend_top_km
                stop
            endif
        endif

        if (taskid == 1) then
            if (waccmx_top_blend_enabled) then
                print *, 'WACCMX neutral top blend policy: linear WACCMX fraction from 1 to 0 between km', &
                         waccmx_top_blend_bottom_km, waccmx_top_blend_top_km
            else
                print *, 'WACCMX neutral top blend policy: none; valid WACCMX cells overwrite native SAMI3'
            endif
        endif

        waccmx_top_blend_initialized = .true.

    end subroutine waccmx_init_top_blend_policy

    real function waccmx_top_blend_alpha(alt_km)

        real, intent(in) :: alt_km

        if (.not. waccmx_top_blend_enabled) then
            waccmx_top_blend_alpha = 1.0
        else if (alt_km <= waccmx_top_blend_bottom_km) then
            waccmx_top_blend_alpha = 1.0
        else if (alt_km >= waccmx_top_blend_top_km) then
            waccmx_top_blend_alpha = 0.0
        else
            waccmx_top_blend_alpha = (waccmx_top_blend_top_km - alt_km) / &
                                     (waccmx_top_blend_top_km - waccmx_top_blend_bottom_km)
        endif

    end function waccmx_top_blend_alpha

    subroutine waccmx_print_recv_qc(header, packet_hour)

        integer, intent(in) :: header(6)
        real, intent(in) :: packet_hour
        integer :: nlocal, valid_i, invalid_i, valid_f, invalid_f
        integer :: he_native_i, he_native_f, w_zero_i, w_zero_f
        integer :: flag_valid, flag_above, flag_n2, flag_other, flag_unknown
        real(kind=8) :: sum_denni, sum_tni, sum_ui, sum_vi, sum_wi
        real(kind=8) :: sum_dennf, sum_tnf, sum_uf, sum_vf, sum_wf

        nlocal = nz*nf*nl
        invalid_i = count(w_denni(:,:,:,pth) < 0.0)
        invalid_f = count(w_dennf(:,:,:,pth) < 0.0)
        valid_i = nlocal - invalid_i
        valid_f = nlocal - invalid_f
        sum_denni = sum(real(w_denni, kind=8))
        sum_tni   = sum(real(w_tni, kind=8))
        sum_ui    = sum(real(w_ui, kind=8))
        sum_vi    = sum(real(w_vi, kind=8))
        sum_wi    = sum(real(w_wi, kind=8))
        sum_dennf = sum(real(w_dennf, kind=8))
        sum_tnf   = sum(real(w_tnf, kind=8))
        sum_uf    = sum(real(w_uf, kind=8))
        sum_vf    = sum(real(w_vf, kind=8))
        sum_wf    = sum(real(w_wf, kind=8))
        he_native_i = valid_i
        he_native_f = valid_f
        w_zero_i = count(w_denni(:,:,:,pth) >= 0.0 .and. w_wi == 0.0)
        w_zero_f = count(w_dennf(:,:,:,pth) >= 0.0 .and. w_wf == 0.0)
        flag_valid = count(w_source_flag == waccmx_flag_valid)
        flag_above = count(w_source_flag == waccmx_flag_above_top)
        flag_n2 = count(w_source_flag == waccmx_flag_n2_invalid)
        flag_other = count(w_source_flag == waccmx_flag_other_invalid)
        flag_unknown = nlocal - flag_valid - flag_above - flag_n2 - flag_other

        print *, 'WACCMX_RECV_QC', taskid, header(6), packet_hour, &
                 valid_i, invalid_i, valid_f, invalid_f, &
                 sum_denni, sum_tni, sum_ui, sum_vi, sum_wi, &
                 sum_dennf, sum_tnf, sum_uf, sum_vf, sum_wf
        print *, 'WACCMX_RECV_SOURCE_FLAGS', taskid, header(6), packet_hour, &
                 nlocal, flag_valid, flag_above, flag_n2, flag_other, &
                 flag_unknown, valid_i, invalid_i, valid_f, invalid_f, &
                 he_native_i, he_native_f, w_zero_i, w_zero_f

    end subroutine waccmx_print_recv_qc

    subroutine waccmx_online_init()

        include 'mpif.h'

        integer :: ierr, unit, ios
        character(len=MPI_MAX_PORT_NAME) :: port_name

        if (.not. lwaccmx_neutral) return
        if (.not. lwaccmx_neutral_online) return
        if (waccmx_online_connected) return

        port_name = ''
        if (taskid == 0) then
            call MPI_Open_port(MPI_INFO_NULL, port_name, ierr)
            if (ierr /= MPI_SUCCESS) then
                print *, 'WACCMX online MPI_Open_port failed ierr=', ierr
                call MPI_Abort(sami3_comm, ierr, ierr)
            endif
            waccmx_online_port_name = port_name
            open(newunit=unit, file=trim(waccmx_online_port_file), &
                 status='replace', action='write', iostat=ios)
            if (ios /= 0) then
                print *, 'WACCMX online port file open failed: ', &
                         trim(waccmx_online_port_file), ios
                call MPI_Abort(sami3_comm, ios, ierr)
            endif
            write(unit,'(A)') trim(port_name)
            close(unit)
            print *, 'WACCMX online port ready: ', trim(waccmx_online_port_file)
        endif
        call MPI_Bcast(port_name, MPI_MAX_PORT_NAME, MPI_CHARACTER, 0, &
                       sami3_comm, ierr)
        if (ierr /= MPI_SUCCESS) then
            print *, 'WACCMX online port name broadcast failed taskid,ierr=', &
                     taskid, ierr
            call MPI_Abort(sami3_comm, ierr, ierr)
        endif

        call MPI_Comm_accept(port_name, MPI_INFO_NULL, 0, sami3_comm, &
                             waccmx_peer_comm, ierr)
        if (ierr /= MPI_SUCCESS) then
            print *, 'WACCMX online MPI_Comm_accept failed taskid,ierr=', &
                     taskid, ierr
            call MPI_Abort(sami3_comm, ierr, ierr)
        endif

        waccmx_online_connected = .true.
        if (taskid == 0) print *, 'WACCMX online sender connected'

    end subroutine waccmx_online_init

    subroutine waccmx_online_finalize()

        include 'mpif.h'

        integer :: ierr, stat, lenval
        integer :: done_value
        character(len=16) :: value

        if (.not. waccmx_online_connected) return

        if (waccmx_online_done_received) then
            done_value = waccmx_online_done_value
        else
            call MPI_Recv(done_value, 1, MPI_INTEGER, 0, waccmx_tag_done, &
                          waccmx_peer_comm, MPI_STATUS_IGNORE, ierr)
            if (ierr /= MPI_SUCCESS) then
                print *, 'WACCMX online done receive failed taskid,ierr=', &
                         taskid, ierr
                call MPI_Abort(sami3_comm, ierr, ierr)
            endif
            waccmx_online_done_received = .true.
            waccmx_online_done_value = done_value
        endif
        if (taskid == 0) print *, 'WACCMX online done signal received:', done_value

        call waccmx_phi_direct_finalize()

        value = ''
        call get_environment_variable('WXSAMI3_SKIP_DISCONNECT', value, length=lenval, status=stat)
        if (stat == 0 .and. lenval > 0 .and. trim(value) == '1') then
            if (taskid == 0 .and. len_trim(waccmx_online_port_name) > 0) then
                call MPI_Close_port(waccmx_online_port_name, ierr)
            endif
            waccmx_online_connected = .false.
            if (taskid == 0) print *, 'WACCMX online disconnect skipped'
            return
        endif

        call MPI_Comm_disconnect(waccmx_peer_comm, ierr)
        if (taskid == 0 .and. len_trim(waccmx_online_port_name) > 0) then
            call MPI_Close_port(waccmx_online_port_name, ierr)
        endif
        waccmx_online_connected = .false.

    end subroutine waccmx_online_finalize

    subroutine waccmx_recv_neutral_online()

        include 'mpif.h'

        integer :: ierr
        integer :: header(6)
        real :: packet_hour
        integer :: nlocal, nlocal4
        integer :: status(MPI_STATUS_SIZE)
        integer :: msg_tag

        if (.not. lwaccmx_neutral_online) return
        if (.not. waccmx_online_connected) then
            print *, 'WACCMX online receive requested before connection: taskid=', taskid
            call MPI_Abort(sami3_comm, 9001, ierr)
        endif
        if (taskid <= 0) return
        if (waccmx_online_done_received) return

        call waccmx_alloc_arrays()
        nlocal = nz*nf*nl
        nlocal4 = nlocal*nneut

        call MPI_Probe(0, MPI_ANY_TAG, waccmx_peer_comm, status, ierr)
        if (ierr /= MPI_SUCCESS) then
            print *, 'WACCMX online probe failed taskid,ierr=', taskid, ierr
            call MPI_Abort(sami3_comm, ierr, ierr)
        endif

        msg_tag = status(MPI_TAG)
        if (msg_tag == waccmx_tag_done) then
            call MPI_Recv(waccmx_online_done_value, 1, MPI_INTEGER, 0, &
                          waccmx_tag_done, waccmx_peer_comm, &
                          MPI_STATUS_IGNORE, ierr)
            if (ierr /= MPI_SUCCESS) then
                print *, 'WACCMX online done receive during neutral failed taskid,ierr=', &
                         taskid, ierr
                call MPI_Abort(sami3_comm, ierr, ierr)
            endif
            waccmx_online_done_received = .true.
            print *, 'WACCMX online done signal received during neutral receive:', &
                     taskid, waccmx_online_done_value
            return
        else if (msg_tag /= waccmx_tag_header) then
            print *, 'WACCMX online unexpected tag while waiting neutral header taskid,tag=', &
                     taskid, msg_tag
            call MPI_Abort(sami3_comm, 9003, ierr)
        endif

        call MPI_Recv(header, 6, MPI_INTEGER, 0, waccmx_tag_header, &
                      waccmx_peer_comm, MPI_STATUS_IGNORE, ierr)
        if (ierr /= MPI_SUCCESS) then
            print *, 'WACCMX online header receive failed taskid,ierr=', taskid, ierr
            call MPI_Abort(sami3_comm, ierr, ierr)
        endif
        if (header(1) /= waccmx_magic .or. header(2) /= nz .or. &
            header(3) /= nf .or. header(4) /= nl .or. &
            header(5) /= nneut) then
            print *, 'WACCMX online header mismatch taskid=', taskid
            print *, 'header=', header
            print *, 'expected=', waccmx_magic, nz, nf, nl, nneut
            call MPI_Abort(sami3_comm, 9002, ierr)
        endif

        call MPI_Recv(packet_hour, 1, MPI_REAL, 0, waccmx_tag_hr, &
                      waccmx_peer_comm, MPI_STATUS_IGNORE, ierr)
        call MPI_Recv(w_denni, nlocal4, MPI_REAL, 0, waccmx_tag_denni, &
                      waccmx_peer_comm, MPI_STATUS_IGNORE, ierr)
        call MPI_Recv(w_tni, nlocal, MPI_REAL, 0, waccmx_tag_tni, &
                      waccmx_peer_comm, MPI_STATUS_IGNORE, ierr)
        call MPI_Recv(w_ui, nlocal, MPI_REAL, 0, waccmx_tag_ui, &
                      waccmx_peer_comm, MPI_STATUS_IGNORE, ierr)
        call MPI_Recv(w_vi, nlocal, MPI_REAL, 0, waccmx_tag_vi, &
                      waccmx_peer_comm, MPI_STATUS_IGNORE, ierr)
        call MPI_Recv(w_wi, nlocal, MPI_REAL, 0, waccmx_tag_wi, &
                      waccmx_peer_comm, MPI_STATUS_IGNORE, ierr)
        call MPI_Recv(w_dennf, nlocal4, MPI_REAL, 0, waccmx_tag_dennf, &
                      waccmx_peer_comm, MPI_STATUS_IGNORE, ierr)
        call MPI_Recv(w_tnf, nlocal, MPI_REAL, 0, waccmx_tag_tnf, &
                      waccmx_peer_comm, MPI_STATUS_IGNORE, ierr)
        call MPI_Recv(w_uf, nlocal, MPI_REAL, 0, waccmx_tag_uf, &
                      waccmx_peer_comm, MPI_STATUS_IGNORE, ierr)
        call MPI_Recv(w_vf, nlocal, MPI_REAL, 0, waccmx_tag_vf, &
                      waccmx_peer_comm, MPI_STATUS_IGNORE, ierr)
        call MPI_Recv(w_wf, nlocal, MPI_REAL, 0, waccmx_tag_wf, &
                      waccmx_peer_comm, MPI_STATUS_IGNORE, ierr)
        call MPI_Recv(w_source_flag, nlocal, MPI_INTEGER, 0, waccmx_tag_source_flags, &
                      waccmx_peer_comm, MPI_STATUS_IGNORE, ierr)

        waccmx_online_packet_count = waccmx_online_packet_count + 1
        waccmx_loaded = .true.
        print *, 'WACCMX online neutral received: taskid,step,packet_hr=', &
                 taskid, header(6), packet_hour
        if (waccmx_recv_qc_enabled()) call waccmx_print_recv_qc(header, packet_hour)

    end subroutine waccmx_recv_neutral_online

    subroutine waccmx_load_neutral(hr)

        real, intent(in) :: hr
        integer :: unit, ios
        integer :: magic_file, nz_file, nf_file, nl_file, nneut_file
        character(len=512) :: fname

        if (.not. lwaccmx_neutral) return
        if (lwaccmx_neutral_online) then
            if (waccmx_loaded .and. abs(hr - waccmx_loaded_request_hr) < 1.0e-6) return
            call waccmx_recv_neutral_online()
            waccmx_loaded_request_hr = hr
            return
        endif
        if (waccmx_loaded) return
        if (taskid <= 0) return

        write(fname,'(A,I4.4,A)') trim(waccmx_neutral_prefix), taskid, '.bin'

        open(newunit=unit, file=trim(fname), form='unformatted', access='stream', &
             status='old', action='read', iostat=ios)
        if (ios /= 0) then
            print *, 'WACCMX neutral open failed: taskid,file,ios=', &
                     taskid, trim(fname), ios
            stop
        endif

        read(unit) magic_file, nz_file, nf_file, nl_file, nneut_file
        if (magic_file /= waccmx_magic .or. nz_file /= nz .or. nf_file /= nf .or. &
            nl_file /= nl .or. nneut_file /= nneut) then
            print *, 'WACCMX neutral header mismatch: taskid,file=', taskid, trim(fname)
            print *, 'file header=', magic_file, nz_file, nf_file, nl_file, nneut_file
            print *, 'expected=', waccmx_magic, nz, nf, nl, nneut
            stop
        endif

        call waccmx_alloc_arrays()

        read(unit) w_denni
        read(unit) w_tni
        read(unit) w_ui
        read(unit) w_vi
        read(unit) w_wi
        read(unit) w_dennf
        read(unit) w_tnf
        read(unit) w_uf
        read(unit) w_vf
        read(unit) w_wf
        close(unit)
        where (w_denni(:,:,:,pth) >= 0.0)
            w_source_flag = waccmx_flag_valid
        elsewhere
            w_source_flag = waccmx_flag_other_invalid
        endwhere

        waccmx_loaded = .true.
        print *, 'WACCMX neutral loaded: taskid,file=', taskid, trim(fname)

    end subroutine waccmx_load_neutral

    subroutine waccmx_apply_neutambt(nll,hr)

        integer, intent(in) :: nll
        real, intent(in) :: hr
        integer :: i, j, k
        integer :: nplane, valid_i, invalid_i, valid_f, invalid_f
        integer :: he_native_i, he_native_f, w_zero_i, w_zero_f
        integer :: flag_valid, flag_above, flag_n2, flag_other, flag_unknown
        integer :: full_i, blend_i, native_top_i
        integer :: full_f, blend_f, native_top_f
        real :: alpha

        if (.not. lwaccmx_neutral) return
        call waccmx_load_neutral(hr)
        if (.not. waccmx_loaded) return
        call waccmx_init_top_blend_policy()

        if (.not. waccmx_apply_policy_logged) then
            if (taskid == 1) then
                print *, 'WACCMX neutral apply policy: negative H density marker retains native SAMI3 neutral state'
                print *, 'WACCMX neutral apply policy: He payload is ignored; SAMI3 native He is retained'
            endif
            waccmx_apply_policy_logged = .true.
        endif

        if (waccmx_recv_qc_enabled()) then
            nplane = nz*nf
            invalid_i = count(w_denni(:,:,nll,pth) < 0.0)
            invalid_f = count(w_dennf(:,:,nll,pth) < 0.0)
            valid_i = nplane - invalid_i
            valid_f = nplane - invalid_f
            he_native_i = valid_i
            he_native_f = valid_f
            w_zero_i = count(w_denni(:,:,nll,pth) >= 0.0 .and. w_wi(:,:,nll) == 0.0)
            w_zero_f = count(w_dennf(:,:,nll,pth) >= 0.0 .and. w_wf(:,:,nll) == 0.0)
            flag_valid = count(w_source_flag(:,:,nll) == waccmx_flag_valid)
            flag_above = count(w_source_flag(:,:,nll) == waccmx_flag_above_top)
            flag_n2 = count(w_source_flag(:,:,nll) == waccmx_flag_n2_invalid)
            flag_other = count(w_source_flag(:,:,nll) == waccmx_flag_other_invalid)
            flag_unknown = nplane - flag_valid - flag_above - flag_n2 - flag_other
            full_i = 0
            blend_i = 0
            native_top_i = 0
            full_f = 0
            blend_f = 0
            native_top_f = 0
            do j = 1,nf
                do i = 1,nz
                    alpha = waccmx_top_blend_alpha(alts(i,j,nll))
                    if (w_denni(i,j,nll,pth) >= 0.0) then
                        if (alpha >= 0.999999) then
                            full_i = full_i + 1
                        else if (alpha <= 0.000001) then
                            native_top_i = native_top_i + 1
                        else
                            blend_i = blend_i + 1
                        endif
                    endif
                    if (w_dennf(i,j,nll,pth) >= 0.0) then
                        if (alpha >= 0.999999) then
                            full_f = full_f + 1
                        else if (alpha <= 0.000001) then
                            native_top_f = native_top_f + 1
                        else
                            blend_f = blend_f + 1
                        endif
                    endif
                enddo
            enddo
            print *, 'WACCMX_APPLY_QC', taskid, nll, hr, nplane, &
                     valid_i, invalid_i, valid_f, invalid_f, &
                     he_native_i, he_native_f, w_zero_i, w_zero_f
            print *, 'WACCMX_APPLY_SOURCE_FLAGS', taskid, nll, hr, nplane, &
                     flag_valid, flag_above, flag_n2, flag_other, flag_unknown
            print *, 'WACCMX_APPLY_BLEND', taskid, nll, hr, nplane, &
                     merge(1, 0, waccmx_top_blend_enabled), &
                     waccmx_top_blend_bottom_km, waccmx_top_blend_top_km, &
                     full_i, blend_i, native_top_i, full_f, blend_f, native_top_f
        endif

        do j = 1,nf
            do i = 1,nz
                alpha = waccmx_top_blend_alpha(alts(i,j,nll))
                if (w_denni(i,j,nll,pth) >= 0.0 .and. alpha > 0.0) then
                    do k = 1,nneut
                        if (k /= pthe) then
                            denni(i,j,nll,k) = alpha*w_denni(i,j,nll,k) + &
                                               (1.0-alpha)*denni(i,j,nll,k)
                        endif
                    enddo
                    tni(i,j,nll) = alpha*w_tni(i,j,nll) + (1.0-alpha)*tni(i,j,nll)
                    ui(i,j,nll)  = alpha*w_ui(i,j,nll)  + (1.0-alpha)*ui(i,j,nll)
                    vi(i,j,nll)  = alpha*w_vi(i,j,nll)  + (1.0-alpha)*vi(i,j,nll)
                    wi(i,j,nll)  = alpha*w_wi(i,j,nll)  + (1.0-alpha)*wi(i,j,nll)
                endif

                if (w_dennf(i,j,nll,pth) >= 0.0 .and. alpha > 0.0) then
                    do k = 1,nneut
                        if (k /= pthe) then
                            dennf(i,j,nll,k) = alpha*w_dennf(i,j,nll,k) + &
                                               (1.0-alpha)*dennf(i,j,nll,k)
                        endif
                    enddo
                    tnf(i,j,nll) = alpha*w_tnf(i,j,nll) + (1.0-alpha)*tnf(i,j,nll)
                    uf(i,j,nll)  = alpha*w_uf(i,j,nll)  + (1.0-alpha)*uf(i,j,nll)
                    vf(i,j,nll)  = alpha*w_vf(i,j,nll)  + (1.0-alpha)*vf(i,j,nll)
                    wf(i,j,nll)  = alpha*w_wf(i,j,nll)  + (1.0-alpha)*wf(i,j,nll)
                endif
            enddo
        enddo

    end subroutine waccmx_apply_neutambt

end module waccmx_neutral_mod
