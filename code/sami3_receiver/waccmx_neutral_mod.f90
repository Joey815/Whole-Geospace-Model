module waccmx_neutral_mod

    use parameter_mod
    use namelist_mod
    use message_passing_mod
    use variable_mod

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
    integer, parameter :: waccmx_tag_done = 299

    logical :: waccmx_loaded = .false.
    logical :: waccmx_online_connected = .false.
    logical :: waccmx_apply_policy_logged = .false.
    integer :: waccmx_peer_comm = -1
    integer :: waccmx_online_packet_count = 0
    real :: waccmx_loaded_request_hr = -1.0e30
    character(len=256) :: waccmx_online_port_name = ''

    real, allocatable :: w_denni(:,:,:,:), w_dennf(:,:,:,:)
    real, allocatable :: w_tni(:,:,:), w_tnf(:,:,:)
    real, allocatable :: w_ui(:,:,:), w_uf(:,:,:)
    real, allocatable :: w_vi(:,:,:), w_vf(:,:,:)
    real, allocatable :: w_wi(:,:,:), w_wf(:,:,:)

contains

    subroutine waccmx_alloc_arrays()

        if (.not. allocated(w_denni)) then
            allocate(w_denni(nz,nf,nl,nneut), w_dennf(nz,nf,nl,nneut))
            allocate(w_tni(nz,nf,nl), w_tnf(nz,nf,nl))
            allocate(w_ui(nz,nf,nl), w_uf(nz,nf,nl))
            allocate(w_vi(nz,nf,nl), w_vf(nz,nf,nl))
            allocate(w_wi(nz,nf,nl), w_wf(nz,nf,nl))
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

    subroutine waccmx_print_recv_qc(header, packet_hour)

        integer, intent(in) :: header(6)
        real, intent(in) :: packet_hour
        integer :: nlocal, valid_i, invalid_i, valid_f, invalid_f
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

        print *, 'WACCMX_RECV_QC', taskid, header(6), packet_hour, &
                 valid_i, invalid_i, valid_f, invalid_f, &
                 sum_denni, sum_tni, sum_ui, sum_vi, sum_wi, &
                 sum_dennf, sum_tnf, sum_uf, sum_vf, sum_wf

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

        call MPI_Recv(done_value, 1, MPI_INTEGER, 0, waccmx_tag_done, &
                      waccmx_peer_comm, MPI_STATUS_IGNORE, ierr)
        if (ierr /= MPI_SUCCESS) then
            print *, 'WACCMX online done receive failed taskid,ierr=', taskid, ierr
            call MPI_Abort(sami3_comm, ierr, ierr)
        endif
        if (taskid == 0) print *, 'WACCMX online done signal received:', done_value

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

        if (.not. lwaccmx_neutral_online) return
        if (.not. waccmx_online_connected) then
            print *, 'WACCMX online receive requested before connection: taskid=', taskid
            call MPI_Abort(sami3_comm, 9001, ierr)
        endif
        if (taskid <= 0) return

        call waccmx_alloc_arrays()
        nlocal = nz*nf*nl
        nlocal4 = nlocal*nneut

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

        waccmx_loaded = .true.
        print *, 'WACCMX neutral loaded: taskid,file=', taskid, trim(fname)

    end subroutine waccmx_load_neutral

    subroutine waccmx_apply_neutambt(nll,hr)

        integer, intent(in) :: nll
        real, intent(in) :: hr
        integer :: i, j, k

        if (.not. lwaccmx_neutral) return
        call waccmx_load_neutral(hr)
        if (.not. waccmx_loaded) return

        if (.not. waccmx_apply_policy_logged) then
            if (taskid == 1) then
                print *, 'WACCMX neutral apply policy: negative H density marker retains native SAMI3 neutral state'
                print *, 'WACCMX neutral apply policy: He payload is ignored; SAMI3 native He is retained'
            endif
            waccmx_apply_policy_logged = .true.
        endif

        do j = 1,nf
            do i = 1,nz
                if (w_denni(i,j,nll,pth) >= 0.0) then
                    do k = 1,nneut
                        if (k /= pthe) denni(i,j,nll,k) = w_denni(i,j,nll,k)
                    enddo
                    tni(i,j,nll) = w_tni(i,j,nll)
                    ui(i,j,nll)  = w_ui(i,j,nll)
                    vi(i,j,nll)  = w_vi(i,j,nll)
                    wi(i,j,nll)  = w_wi(i,j,nll)
                endif

                if (w_dennf(i,j,nll,pth) >= 0.0) then
                    do k = 1,nneut
                        if (k /= pthe) dennf(i,j,nll,k) = w_dennf(i,j,nll,k)
                    enddo
                    tnf(i,j,nll) = w_tnf(i,j,nll)
                    uf(i,j,nll)  = w_uf(i,j,nll)
                    vf(i,j,nll)  = w_vf(i,j,nll)
                    wf(i,j,nll)  = w_wf(i,j,nll)
                endif
            enddo
        enddo

    end subroutine waccmx_apply_neutambt

end module waccmx_neutral_mod
