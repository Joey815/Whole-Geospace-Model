module wxsami3_online_stub_mod

   use shr_kind_mod,    only: r8 => SHR_KIND_R8
   use spmd_utils,      only: masterproc, mpicom
   use cam_logfile,     only: iulog
   use cam_abortutils,  only: endrun
   use physics_types,   only: physics_state
   use ppgrid,          only: pver
   use constituents,    only: cnst_get_ind, cnst_name, cnst_mw, cnst_type
   use air_composition, only: mbarv

   implicit none
   private

   public :: wxsami3_cam_send
   public :: wxsami3_cam_finalize

   integer, parameter :: tag_header = 200
   integer, parameter :: tag_hr     = 201
   integer, parameter :: tag_denni  = 202
   integer, parameter :: tag_tni    = 203
   integer, parameter :: tag_ui     = 204
   integer, parameter :: tag_vi     = 205
   integer, parameter :: tag_wi     = 206
   integer, parameter :: tag_dennf  = 207
   integer, parameter :: tag_tnf    = 208
   integer, parameter :: tag_uf     = 209
   integer, parameter :: tag_vf     = 210
   integer, parameter :: tag_wf     = 211
   integer, parameter :: tag_done   = 299

   logical :: is_initialized = .false.
   logical :: is_enabled = .false.
   logical :: is_connected = .false.
   integer :: peer_comm = -1
   integer :: num_workers = 32
   integer :: packet_count = 0
   integer :: max_packets = -1
   integer :: send_every_nsteps = 1
   integer :: cadence_skip_count = 0
   logical :: live_payload_mode = .false.
   logical :: live_diag_enabled = .false.
   logical :: live_registry_logged = .false.
   logical :: live_dump_enabled = .false.
   logical :: live_dump_meta_written = .false.
   logical :: max_packets_logged = .false.
   integer :: live_dump_max = 1
   character(len=512) :: port_file = ''
   character(len=512) :: payload_prefix = ''
   character(len=32) :: payload_mode = 'file'
   character(len=16) :: n2_negative_mode = 'floor'
   character(len=512) :: meta_file = ''
   character(len=512) :: live_dump_prefix = ''
   character(len=512) :: live_map_file = ''

   integer, parameter :: payload_magic = 20260522
   integer, parameter :: live_map_magic = 20260524
   integer, parameter :: sami_nz = 304
   integer, parameter :: sami_nf = 124
   integer, parameter :: sami_nl = 5
   integer, parameter :: sami_nlt = 96
   integer, parameter :: sami_nneut = 7
   integer, parameter :: sami_nlocal = sami_nz * sami_nf * sami_nl
   integer, parameter :: sami_nlocal4 = sami_nlocal * sami_nneut
   integer, parameter :: n_live_fields = 12
   integer, parameter :: n_live_species = 7
   integer, parameter :: n_dump_profile = 7
   integer, parameter :: live_dump_magic = 20260523
   character(len=8), parameter :: live_species(n_live_species) = &
      (/ 'O       ', 'O2      ', 'H       ', 'N       ', 'NO      ', 'N2      ', 'He      ' /)
   real(r8), parameter :: live_species_mw(n_live_species) = &
      (/ 16._r8, 32._r8, 1._r8, 14._r8, 30._r8, 28._r8, 4._r8 /)
   real(r8), parameter :: kb_si = 1.380649e-23_r8
   real(r8), parameter :: rad_to_deg = 57.2957795130823208768_r8

   logical :: live_map_loaded = .false.
   integer :: live_map_npoints = 0
   integer :: live_map_ns = 0
   integer :: live_map_nsource = 0
   real, allocatable :: live_map_zalt(:)
   integer, allocatable :: live_map_row_start(:), live_map_row_count(:), live_map_col(:)
   real(r8), allocatable :: live_map_s(:)

contains

   subroutine wxsami3_init()

      integer :: stat, lenval
      character(len=512) :: value

      if (is_initialized) return
      is_initialized = .true.

      call get_environment_variable('WXSAMI3_PORT_FILE', port_file, length=lenval, status=stat)
      if (stat /= 0 .or. lenval <= 0) then
         is_enabled = .false.
         return
      endif

      payload_mode = 'file'
      value = ''
      call get_environment_variable('WXSAMI3_PAYLOAD_MODE', value, length=lenval, status=stat)
      if (stat == 0 .and. lenval > 0) payload_mode = adjustl(value(1:lenval))
      live_payload_mode = trim(payload_mode) == 'live' .or. trim(payload_mode) == 'LIVE'

      call get_environment_variable('WXSAMI3_PAYLOAD_PREFIX', payload_prefix, length=lenval, status=stat)
      if ((stat /= 0 .or. lenval <= 0) .and. .not. live_payload_mode) then
         call endrun('WXSAMI3_PORT_FILE is set but WXSAMI3_PAYLOAD_PREFIX is missing')
      endif
      if (stat /= 0 .or. lenval <= 0) payload_prefix = ''

      live_map_file = ''
      call get_environment_variable('WXSAMI3_LIVE_MAP_FILE', live_map_file, length=lenval, status=stat)
      if (live_payload_mode .and. (stat /= 0 .or. lenval <= 0)) then
         call endrun('WXSAMI3_PAYLOAD_MODE=live requires WXSAMI3_LIVE_MAP_FILE')
      endif

      value = ''
      call get_environment_variable('WXSAMI3_NUMWORKERS', value, length=lenval, status=stat)
      if (stat == 0 .and. lenval > 0) read(value,*) num_workers

      value = ''
      call get_environment_variable('WXSAMI3_LIVE_DIAG', value, length=lenval, status=stat)
      if (stat == 0 .and. lenval > 0) then
         live_diag_enabled = trim(value) == '1' .or. trim(value) == 'true' .or. &
                             trim(value) == 'TRUE' .or. trim(value) == 'yes'
      endif

      meta_file = ''
      call get_environment_variable('WXSAMI3_META_FILE', meta_file, length=lenval, status=stat)
      if (stat /= 0 .or. lenval <= 0) meta_file = ''

      live_dump_prefix = ''
      call get_environment_variable('WXSAMI3_LIVE_DUMP_PREFIX', live_dump_prefix, length=lenval, status=stat)
      if (stat == 0 .and. lenval > 0) live_dump_enabled = .true.

      value = ''
      call get_environment_variable('WXSAMI3_LIVE_DUMP_MAX', value, length=lenval, status=stat)
      if (stat == 0 .and. lenval > 0) read(value,*) live_dump_max
      if (live_dump_max < 0) live_dump_max = 0

      value = ''
      call get_environment_variable('WXSAMI3_MAX_PACKETS', value, length=lenval, status=stat)
      if (stat == 0 .and. lenval > 0) read(value,*) max_packets
      if (max_packets < 0) max_packets = -1

      value = ''
      call get_environment_variable('WXSAMI3_SEND_EVERY_NSTEPS', value, length=lenval, status=stat)
      if (stat == 0 .and. lenval > 0) read(value,*) send_every_nsteps
      if (send_every_nsteps < 1) send_every_nsteps = 1

      value = ''
      call get_environment_variable('WXSAMI3_N2_NEGATIVE_MODE', value, length=lenval, status=stat)
      if (stat == 0 .and. lenval > 0) n2_negative_mode = adjustl(value(1:min(lenval, len(n2_negative_mode))))
      select case (trim(n2_negative_mode))
      case ('floor', 'FLOOR', 'invalid', 'INVALID', 'fail', 'FAIL')
      case default
         call endrun('WXSAMI3_N2_NEGATIVE_MODE must be floor, invalid, or fail')
      end select

      is_enabled = .true.
      if (masterproc) then
         write(iulog,*) 'WXSAMI3 online sender enabled'
         write(iulog,*) 'WXSAMI3 port file: ', trim(port_file)
         write(iulog,*) 'WXSAMI3 payload mode: ', trim(payload_mode)
         if (len_trim(payload_prefix) > 0) write(iulog,*) 'WXSAMI3 payload prefix: ', trim(payload_prefix)
         if (len_trim(live_map_file) > 0) write(iulog,*) 'WXSAMI3 live map file: ', trim(live_map_file)
         write(iulog,*) 'WXSAMI3 SAMI3 workers: ', num_workers
         write(iulog,*) 'WXSAMI3 send cadence nsteps: ', send_every_nsteps
         write(iulog,*) 'WXSAMI3 max packets (-1 unlimited): ', max_packets
         write(iulog,*) 'WXSAMI3 N2 negative residual mode: ', trim(n2_negative_mode)
         write(iulog,*) 'WXSAMI3 live phys_state diagnostics: ', live_diag_enabled
         if (len_trim(meta_file) > 0) write(iulog,*) 'WXSAMI3 metadata file: ', trim(meta_file)
         write(iulog,*) 'WXSAMI3 live state dump enabled: ', live_dump_enabled
         if (live_dump_enabled) then
            write(iulog,*) 'WXSAMI3 live state dump prefix: ', trim(live_dump_prefix)
            write(iulog,*) 'WXSAMI3 live state dump max packets: ', live_dump_max
         endif
      endif

   end subroutine wxsami3_init

   subroutine wxsami3_connect()

      include 'mpif.h'

      integer :: ierr, ios
      character(len=MPI_MAX_PORT_NAME) :: port_name

      if (is_connected) return
      if (.not. is_enabled) return

      port_name = ''
      if (masterproc) then
         open(unit=119, file=trim(port_file), status='old', action='read', iostat=ios)
         if (ios /= 0) then
            call endrun('WXSAMI3 failed to open SAMI3 MPI port file')
         endif
         read(119,'(A)',iostat=ios) port_name
         close(119)
         if (ios /= 0 .or. len_trim(port_name) == 0) then
            call endrun('WXSAMI3 failed to read SAMI3 MPI port')
         endif
         write(iulog,*) 'WXSAMI3 connecting to SAMI3 online port'
      endif

      call MPI_Comm_connect(port_name, MPI_INFO_NULL, 0, mpicom, peer_comm, ierr)
      if (ierr /= MPI_SUCCESS) then
         call endrun('WXSAMI3 MPI_Comm_connect failed')
      endif

      is_connected = .true.
      if (masterproc) write(iulog,*) 'WXSAMI3 connected to SAMI3'

   end subroutine wxsami3_connect

   subroutine wxsami3_cam_send(nstep, dtime_phys, state)

      integer, intent(in) :: nstep
      real(r8), intent(in) :: dtime_phys
      type(physics_state), intent(in) :: state(:)
      integer :: worker
      real :: packet_hour

      call wxsami3_init()
      if (.not. is_enabled) return

      if (max_packets >= 0 .and. packet_count >= max_packets) then
         if (masterproc .and. .not. max_packets_logged) then
            write(iulog,*) 'WXSAMI3 max packets reached; skipping further sends: ', &
                           packet_count, max_packets
         endif
         max_packets_logged = .true.
         return
      endif

      if (send_every_nsteps > 1 .and. mod(nstep, send_every_nsteps) /= 0) then
         cadence_skip_count = cadence_skip_count + 1
         if (masterproc .and. (cadence_skip_count <= 3 .or. mod(cadence_skip_count,100) == 0)) then
            write(iulog,*) 'WXSAMI3 cadence skip: nstep,send_every,skipped=', &
                           nstep, send_every_nsteps, cadence_skip_count
         endif
         return
      endif

      if (live_diag_enabled) call wxsami3_live_neutral_diag(state, nstep, dtime_phys)
      if (live_dump_enabled .and. packet_count < live_dump_max) then
         call wxsami3_dump_live_state(state, nstep, dtime_phys)
      endif

      call wxsami3_connect()

      packet_hour = real(nstep) * real(dtime_phys) / 3600.0
      if (live_payload_mode) then
         call wxsami3_send_live_packet(nstep, dtime_phys, packet_hour, state)
      else if (masterproc) then
         do worker = 1, num_workers
            call wxsami3_send_worker(worker, nstep, packet_hour)
         enddo
         write(iulog,*) 'WXSAMI3 sent neutral packet: nstep,packet_hour,count=', &
                        nstep, packet_hour, packet_count
      endif
      packet_count = packet_count + 1

   end subroutine wxsami3_cam_send

   subroutine wxsami3_live_neutral_diag(state, nstep, dtime_phys)

      include 'mpif.h'

      type(physics_state), intent(in) :: state(:)
      integer, intent(in) :: nstep
      real(r8), intent(in) :: dtime_phys

      integer :: ierr
      integer :: live_ind(n_live_species)
      integer :: ispc
      real(r8) :: local_min, local_max, global_min, global_max
      integer :: local_bad, global_bad
      integer :: local_neg, global_neg
      real(r8) :: residual_min, residual_max
      real(r8) :: residual_global_min, residual_global_max

      call wxsami3_get_species_indices(live_ind)

      if (.not. live_registry_logged) then
         call wxsami3_log_live_registry(live_ind)
         live_registry_logged = .true.
      endif

      if (masterproc) then
         write(iulog,*) 'WXSAMI3 live neutral diagnostic packet nstep,dtime=', nstep, dtime_phys
         write(iulog,*) 'WXSAMI3 live units: lat/lon=deg T=K U/V=m/s omega=Pa/s pmid=Pa zm/zi=m q=mass_mixing_ratio'
         write(iulog,*) 'WXSAMI3 live density conversion: q*mbarv/species_mw*pmid/(kB*T)*1e-6 -> cm^-3'
      endif

      call wxsami3_reduce_column_count(state)
      call wxsami3_reduce_coord1d(state, 'LAT', 'deg', coord_id=1)
      call wxsami3_reduce_coord1d(state, 'LON', 'deg', coord_id=2)
      call wxsami3_reduce_cid(state)
      call wxsami3_reduce_field2d(state, 'T', 'K', field_id=1)
      call wxsami3_reduce_field2d(state, 'U', 'm/s', field_id=2)
      call wxsami3_reduce_field2d(state, 'V', 'm/s', field_id=3)
      call wxsami3_reduce_field2d(state, 'OMEGA', 'Pa/s', field_id=4)
      call wxsami3_reduce_field2d(state, 'PMID', 'Pa', field_id=5)
      call wxsami3_reduce_field2d(state, 'ZM', 'm', field_id=6)

      do ispc = 1, n_live_species
         if (live_ind(ispc) > 0) then
            call wxsami3_species_q_stats(state, live_ind(ispc), local_min, local_max, local_bad)
            call MPI_Reduce(local_min, global_min, 1, MPI_DOUBLE_PRECISION, MPI_MIN, 0, mpicom, ierr)
            call MPI_Reduce(local_max, global_max, 1, MPI_DOUBLE_PRECISION, MPI_MAX, 0, mpicom, ierr)
            call MPI_Reduce(local_bad, global_bad, 1, MPI_INTEGER, MPI_SUM, 0, mpicom, ierr)
            if (masterproc) then
               write(iulog,*) 'WXSAMI3 live q species,index,min,max,bad=', &
                  trim(live_species(ispc)), live_ind(ispc), global_min, global_max, global_bad
            endif

            if (allocated(mbarv)) then
               call wxsami3_species_density_stats(state, live_ind(ispc), live_species_mw(ispc), &
                  local_min, local_max, local_bad)
               call MPI_Reduce(local_min, global_min, 1, MPI_DOUBLE_PRECISION, MPI_MIN, 0, mpicom, ierr)
               call MPI_Reduce(local_max, global_max, 1, MPI_DOUBLE_PRECISION, MPI_MAX, 0, mpicom, ierr)
               call MPI_Reduce(local_bad, global_bad, 1, MPI_INTEGER, MPI_SUM, 0, mpicom, ierr)
               if (masterproc) then
                  write(iulog,*) 'WXSAMI3 live ndens_cm3 species,min,max,bad=', &
                     trim(live_species(ispc)), global_min, global_max, global_bad
               endif
            endif
         endif
      enddo

      call wxsami3_n2_residual_stats(state, live_ind, residual_min, residual_max, local_neg, local_bad)
      call MPI_Reduce(residual_min, residual_global_min, 1, MPI_DOUBLE_PRECISION, MPI_MIN, 0, mpicom, ierr)
      call MPI_Reduce(residual_max, residual_global_max, 1, MPI_DOUBLE_PRECISION, MPI_MAX, 0, mpicom, ierr)
      call MPI_Reduce(local_neg, global_neg, 1, MPI_INTEGER, MPI_SUM, 0, mpicom, ierr)
      call MPI_Reduce(local_bad, global_bad, 1, MPI_INTEGER, MPI_SUM, 0, mpicom, ierr)
      if (masterproc) then
         write(iulog,*) 'WXSAMI3 live N2 residual major min,max,negative,bad=', &
            residual_global_min, residual_global_max, global_neg, global_bad
      endif

      if (masterproc .and. len_trim(meta_file) > 0) call wxsami3_write_meta(nstep, dtime_phys, live_ind)

   end subroutine wxsami3_live_neutral_diag

   subroutine wxsami3_get_species_indices(live_ind)

      integer, intent(out) :: live_ind(n_live_species)
      integer :: i

      do i = 1, n_live_species
         call cnst_get_ind(trim(live_species(i)), live_ind(i), abort=.false.)
      enddo
      if (live_ind(7) <= 0) call cnst_get_ind('HE', live_ind(7), abort=.false.)

   end subroutine wxsami3_get_species_indices

   subroutine wxsami3_log_live_registry(live_ind)

      integer, intent(in) :: live_ind(n_live_species)
      integer :: i

      if (.not. masterproc) return

      write(iulog,*) 'WXSAMI3 live neutral constituent registry begin'
      do i = 1, n_live_species
         if (live_ind(i) > 0) then
            write(iulog,*) 'WXSAMI3 live species,index,name,type,mw,sent=', &
               trim(live_species(i)), live_ind(i), trim(cnst_name(live_ind(i))), &
               trim(cnst_type(live_ind(i))), cnst_mw(live_ind(i)), .true.
         else
            write(iulog,*) 'WXSAMI3 live species,index,name,type,mw,sent=', &
               trim(live_species(i)), live_ind(i), 'MISSING', 'none', live_species_mw(i), .false.
         endif
      enddo
      write(iulog,*) 'WXSAMI3 live neutral constituent registry end'

   end subroutine wxsami3_log_live_registry

   subroutine wxsami3_reduce_column_count(state)

      include 'mpif.h'

      type(physics_state), intent(in) :: state(:)

      integer :: ierr
      integer :: lchnk
      integer :: local_cols, global_cols

      local_cols = 0
      do lchnk = lbound(state, 1), ubound(state, 1)
         local_cols = local_cols + state(lchnk)%ncol
      enddo

      call MPI_Reduce(local_cols, global_cols, 1, MPI_INTEGER, MPI_SUM, 0, mpicom, ierr)
      if (masterproc) write(iulog,*) 'WXSAMI3 live physics columns global=', global_cols

   end subroutine wxsami3_reduce_column_count

   subroutine wxsami3_reduce_coord1d(state, label, units, coord_id)

      include 'mpif.h'

      type(physics_state), intent(in) :: state(:)
      character(len=*), intent(in) :: label
      character(len=*), intent(in) :: units
      integer, intent(in) :: coord_id

      integer :: ierr
      real(r8) :: local_min, local_max, global_min, global_max
      integer :: local_bad, global_bad

      call wxsami3_coord1d_stats(state, coord_id, local_min, local_max, local_bad)
      call MPI_Reduce(local_min, global_min, 1, MPI_DOUBLE_PRECISION, MPI_MIN, 0, mpicom, ierr)
      call MPI_Reduce(local_max, global_max, 1, MPI_DOUBLE_PRECISION, MPI_MAX, 0, mpicom, ierr)
      call MPI_Reduce(local_bad, global_bad, 1, MPI_INTEGER, MPI_SUM, 0, mpicom, ierr)

      if (masterproc) then
         write(iulog,*) 'WXSAMI3 live coord,min,max,bad,units=', &
            trim(label), global_min, global_max, global_bad, trim(units)
      endif

   end subroutine wxsami3_reduce_coord1d

   subroutine wxsami3_coord1d_stats(state, coord_id, field_min, field_max, bad_count)

      type(physics_state), intent(in) :: state(:)
      integer, intent(in) :: coord_id
      real(r8), intent(out) :: field_min, field_max
      integer, intent(out) :: bad_count

      integer :: lchnk, i, ncol
      real(r8) :: value

      field_min = huge(1._r8)
      field_max = -huge(1._r8)
      bad_count = 0

      do lchnk = lbound(state, 1), ubound(state, 1)
         ncol = state(lchnk)%ncol
         if ((coord_id == 1 .and. .not. allocated(state(lchnk)%lat)) .or. &
             (coord_id == 2 .and. .not. allocated(state(lchnk)%lon))) then
            bad_count = bad_count + ncol
         else
            do i = 1, ncol
               select case (coord_id)
               case (1)
                  value = state(lchnk)%lat(i) * rad_to_deg
               case (2)
                  value = state(lchnk)%lon(i) * rad_to_deg
               case default
                  value = huge(1._r8)
               end select
               call wxsami3_update_minmax(value, field_min, field_max, bad_count)
            enddo
         endif
      enddo

   end subroutine wxsami3_coord1d_stats

   subroutine wxsami3_reduce_cid(state)

      include 'mpif.h'

      type(physics_state), intent(in) :: state(:)

      integer :: ierr
      integer :: lchnk, i, ncol
      integer :: local_min, local_max, global_min, global_max
      integer :: local_bad, global_bad

      local_min = huge(1)
      local_max = -huge(1)
      local_bad = 0

      do lchnk = lbound(state, 1), ubound(state, 1)
         ncol = state(lchnk)%ncol
         if (.not. allocated(state(lchnk)%cid)) then
            local_bad = local_bad + ncol
         else
            do i = 1, ncol
               local_min = min(local_min, state(lchnk)%cid(i))
               local_max = max(local_max, state(lchnk)%cid(i))
            enddo
         endif
      enddo

      call MPI_Reduce(local_min, global_min, 1, MPI_INTEGER, MPI_MIN, 0, mpicom, ierr)
      call MPI_Reduce(local_max, global_max, 1, MPI_INTEGER, MPI_MAX, 0, mpicom, ierr)
      call MPI_Reduce(local_bad, global_bad, 1, MPI_INTEGER, MPI_SUM, 0, mpicom, ierr)
      if (masterproc) write(iulog,*) 'WXSAMI3 live column id min,max,bad=', global_min, global_max, global_bad

   end subroutine wxsami3_reduce_cid

   subroutine wxsami3_reduce_field2d(state, label, units, field_id)

      include 'mpif.h'

      type(physics_state), intent(in) :: state(:)
      character(len=*), intent(in) :: label
      character(len=*), intent(in) :: units
      integer, intent(in) :: field_id

      integer :: ierr
      real(r8) :: local_min, local_max, global_min, global_max
      integer :: local_bad, global_bad

      call wxsami3_field2d_stats(state, field_id, local_min, local_max, local_bad)
      call MPI_Reduce(local_min, global_min, 1, MPI_DOUBLE_PRECISION, MPI_MIN, 0, mpicom, ierr)
      call MPI_Reduce(local_max, global_max, 1, MPI_DOUBLE_PRECISION, MPI_MAX, 0, mpicom, ierr)
      call MPI_Reduce(local_bad, global_bad, 1, MPI_INTEGER, MPI_SUM, 0, mpicom, ierr)

      if (masterproc) then
         write(iulog,*) 'WXSAMI3 live field,min,max,bad,units=', &
            trim(label), global_min, global_max, global_bad, trim(units)
      endif

   end subroutine wxsami3_reduce_field2d

   subroutine wxsami3_field2d_stats(state, field_id, field_min, field_max, bad_count)

      type(physics_state), intent(in) :: state(:)
      integer, intent(in) :: field_id
      real(r8), intent(out) :: field_min, field_max
      integer, intent(out) :: bad_count

      integer :: lchnk, i, k, ncol
      real(r8) :: value

      field_min = huge(1._r8)
      field_max = -huge(1._r8)
      bad_count = 0

      do lchnk = lbound(state, 1), ubound(state, 1)
         ncol = state(lchnk)%ncol
         do k = 1, pver
            do i = 1, ncol
               select case (field_id)
               case (1)
                  value = state(lchnk)%t(i,k)
               case (2)
                  value = state(lchnk)%u(i,k)
               case (3)
                  value = state(lchnk)%v(i,k)
               case (4)
                  value = state(lchnk)%omega(i,k)
               case (5)
                  value = state(lchnk)%pmid(i,k)
               case (6)
                  value = state(lchnk)%zm(i,k)
               end select
               call wxsami3_update_minmax(value, field_min, field_max, bad_count)
            enddo
         enddo
      enddo

   end subroutine wxsami3_field2d_stats

   subroutine wxsami3_species_q_stats(state, qind, field_min, field_max, bad_count)

      type(physics_state), intent(in) :: state(:)
      integer, intent(in) :: qind
      real(r8), intent(out) :: field_min, field_max
      integer, intent(out) :: bad_count

      integer :: lchnk, i, k, ncol
      real(r8) :: value

      field_min = huge(1._r8)
      field_max = -huge(1._r8)
      bad_count = 0

      do lchnk = lbound(state, 1), ubound(state, 1)
         ncol = state(lchnk)%ncol
         do k = 1, pver
            do i = 1, ncol
               value = state(lchnk)%q(i,k,qind)
               call wxsami3_update_minmax(value, field_min, field_max, bad_count)
            enddo
         enddo
      enddo

   end subroutine wxsami3_species_q_stats

   subroutine wxsami3_species_density_stats(state, qind, species_mw, field_min, field_max, bad_count)

      type(physics_state), intent(in) :: state(:)
      integer, intent(in) :: qind
      real(r8), intent(in) :: species_mw
      real(r8), intent(out) :: field_min, field_max
      integer, intent(out) :: bad_count

      integer :: lchnk, i, k, ncol, chunk_id
      real(r8) :: value

      field_min = huge(1._r8)
      field_max = -huge(1._r8)
      bad_count = 0

      do lchnk = lbound(state, 1), ubound(state, 1)
         chunk_id = state(lchnk)%lchnk
         ncol = state(lchnk)%ncol
         do k = 1, pver
            do i = 1, ncol
               value = state(lchnk)%q(i,k,qind) * mbarv(i,k,chunk_id) / species_mw * &
                       state(lchnk)%pmid(i,k) / (kb_si * state(lchnk)%t(i,k)) * 1.0e-6_r8
               call wxsami3_update_minmax(value, field_min, field_max, bad_count)
            enddo
         enddo
      enddo

   end subroutine wxsami3_species_density_stats

   subroutine wxsami3_n2_residual_stats(state, live_ind, field_min, field_max, neg_count, bad_count)

      type(physics_state), intent(in) :: state(:)
      integer, intent(in) :: live_ind(n_live_species)
      real(r8), intent(out) :: field_min, field_max
      integer, intent(out) :: neg_count, bad_count

      integer :: lchnk, i, k, ispc, ncol
      real(r8) :: value

      field_min = huge(1._r8)
      field_max = -huge(1._r8)
      neg_count = 0
      bad_count = 0

      do lchnk = lbound(state, 1), ubound(state, 1)
         ncol = state(lchnk)%ncol
         do k = 1, pver
            do i = 1, ncol
               value = 1._r8
               do ispc = 1, 5
                  if (live_ind(ispc) > 0) value = value - state(lchnk)%q(i,k,live_ind(ispc))
               enddo
               if (value < 0._r8) neg_count = neg_count + 1
               call wxsami3_update_minmax(value, field_min, field_max, bad_count)
            enddo
         enddo
      enddo

   end subroutine wxsami3_n2_residual_stats

   subroutine wxsami3_update_minmax(value, field_min, field_max, bad_count)

      real(r8), intent(in) :: value
      real(r8), intent(inout) :: field_min, field_max
      integer, intent(inout) :: bad_count

      if (value /= value .or. abs(value) >= huge(1._r8) * 0.5_r8) then
         bad_count = bad_count + 1
      else
         field_min = min(field_min, value)
         field_max = max(field_max, value)
      endif

   end subroutine wxsami3_update_minmax

   subroutine wxsami3_write_meta(nstep, dtime_phys, live_ind)

      integer, intent(in) :: nstep
      real(r8), intent(in) :: dtime_phys
      integer, intent(in) :: live_ind(n_live_species)

      integer :: ios, ispc

      open(unit=118, file=trim(meta_file), status='replace', action='write', iostat=ios)
      if (ios /= 0) then
         write(iulog,*) 'WXSAMI3 warning: failed to write metadata file: ', trim(meta_file)
         return
      endif

      write(118,'(A)') '{'
      write(118,'(A)') '  "payload_version": "wxsami3-live-diag-v1",'
      write(118,'(A,A,A)') '  "payload_mode": "', trim(payload_mode), '",'
      write(118,'(A,I0,A)') '  "nstep": ', nstep, ','
      write(118,'(A,ES24.16,A)') '  "dtime_phys_s": ', dtime_phys, ','
      if (live_payload_mode) then
         write(118,'(A)') '  "actual_transport": "runtime_live_packet",'
      else
         write(118,'(A)') '  "actual_transport": "file_backed_payload_fallback",'
      endif
      write(118,'(A)') '  "runtime_source": "CAM phys_state(:)",'
      write(118,'(A,I0,A)') '  "send_every_nsteps": ', send_every_nsteps, ','
      write(118,'(A,I0,A)') '  "max_packets": ', max_packets, ','
      write(118,'(A,I0,A)') '  "sami_horizontal_points": ', sami_nf * sami_nlt, ','
      write(118,'(A,I0,A)') '  "sami_nz": ', sami_nz, ','
      write(118,'(A,I0,A)') '  "sami_nf": ', sami_nf, ','
      write(118,'(A,I0,A)') '  "sami_nl": ', sami_nl, ','
      write(118,'(A,I0,A)') '  "sami_nlt": ', sami_nlt, ','
      write(118,'(A)') '  "temperature_unit": "K",'
      write(118,'(A)') '  "wind_unit": "m/s",'
      write(118,'(A)') '  "pressure_unit": "Pa",'
      write(118,'(A)') '  "payload_density_unit": "cm^-3",'
      write(118,'(A)') '  "payload_wind_unit": "cm/s",'
      write(118,'(A)') '  "height_source": "physics_state%zm and physics_state%zi, geopotential height above surface, m",'
      write(118,'(A)') '  "composition_source": "physics_state%q mass mixing ratio",'
      write(118,'(A)') '  "density_conversion": "q*mbarv/species_mw*pmid/(kB*T)*1e-6 -> cm^-3",'
      write(118,'(A)') '  "vertical_wind_policy": "W not sent; omega diagnosed only",'
      write(118,'(A,A,A)') '  "n2_negative_mode": "', trim(n2_negative_mode), '",'
      write(118,'(A)') '  "payload_species_order": ["H","O","NO","O2","He","N2","N"],'
      write(118,'(A)') '  "fallback_policy": "above-live-top samples invalid; He payload=-1 native fallback; W payload=0",'
      write(118,'(A)') '  "species": ['
      do ispc = 1, n_live_species
         if (ispc < n_live_species) then
            write(118,'(A,A,A,I0,A)') '    {"name":"', trim(live_species(ispc)), '","index":', live_ind(ispc), '},'
         else
            write(118,'(A,A,A,I0,A)') '    {"name":"', trim(live_species(ispc)), '","index":', live_ind(ispc), '}'
         endif
      enddo
      write(118,'(A)') '  ]'
      write(118,'(A)') '}'
      close(118)

   end subroutine wxsami3_write_meta

   subroutine wxsami3_write_live_packet_meta(nstep, dtime_phys, packet_hour, live_ind, &
                                             samples, invalid, above_top, n2_used, &
                                             n2_negative, n2_min, n2_max, valid_i, &
                                             invalid_i, valid_f, invalid_f, payload_sums)

      integer, intent(in) :: nstep
      real(r8), intent(in) :: dtime_phys
      real, intent(in) :: packet_hour
      integer, intent(in) :: live_ind(n_live_species)
      integer, intent(in) :: samples, invalid, above_top, n2_used, n2_negative
      integer, intent(in) :: valid_i, invalid_i, valid_f, invalid_f
      real(r8), intent(in) :: n2_min, n2_max, payload_sums(10)

      integer :: ios, ispc

      open(unit=118, file=trim(meta_file), status='replace', action='write', iostat=ios)
      if (ios /= 0) then
         write(iulog,*) 'WXSAMI3 warning: failed to write live packet metadata file: ', trim(meta_file)
         return
      endif

      write(118,'(A)') '{'
      write(118,'(A)') '  "payload_version": "wxsami3-live-payload-v2",'
      write(118,'(A,A,A)') '  "payload_mode": "', trim(payload_mode), '",'
      write(118,'(A)') '  "actual_transport": "runtime_live_packet",'
      write(118,'(A)') '  "runtime_source": "CAM phys_state(:)",'
      write(118,'(A,I0,A)') '  "send_every_nsteps": ', send_every_nsteps, ','
      write(118,'(A,I0,A)') '  "max_packets": ', max_packets, ','
      write(118,'(A,I0,A)') '  "nstep": ', nstep, ','
      write(118,'(A,ES24.16,A)') '  "dtime_phys_s": ', dtime_phys, ','
      write(118,'(A,ES16.8,A)') '  "packet_hour": ', real(packet_hour, r8), ','
      write(118,'(A,I0,A)') '  "packet_index": ', packet_count, ','
      write(118,'(A)') '  "payload_header": {'
      write(118,'(A,I0,A)') '    "magic": ', payload_magic, ','
      write(118,'(A,I0,A)') '    "nz": ', sami_nz, ','
      write(118,'(A,I0,A)') '    "nf": ', sami_nf, ','
      write(118,'(A,I0,A)') '    "nl": ', sami_nl, ','
      write(118,'(A,I0,A)') '    "nneut": ', sami_nneut
      write(118,'(A)') '  },'
      write(118,'(A)') '  "runtime_map": {'
      write(118,'(A,A,A)') '    "file": "', trim(live_map_file), '",'
      write(118,'(A,I0,A)') '    "magic": ', live_map_magic, ','
      write(118,'(A,I0,A)') '    "npoints": ', live_map_npoints, ','
      write(118,'(A,I0,A)') '    "n_s": ', live_map_ns, ','
      write(118,'(A,I0,A)') '    "source_columns": ', live_map_nsource
      write(118,'(A)') '  },'
      write(118,'(A)') '  "source_units": {'
      write(118,'(A)') '    "temperature": "K",'
      write(118,'(A)') '    "wind": "m/s",'
      write(118,'(A)') '    "omega": "Pa/s diagnostic only",'
      write(118,'(A)') '    "pressure": "Pa",'
      write(118,'(A)') '    "height": "m",'
      write(118,'(A)') '    "composition": "mass_mixing_ratio"'
      write(118,'(A)') '  },'
      write(118,'(A)') '  "payload_units": {'
      write(118,'(A)') '    "density": "cm^-3",'
      write(118,'(A)') '    "temperature": "K",'
      write(118,'(A)') '    "wind": "cm/s"'
      write(118,'(A)') '  },'
      write(118,'(A)') '  "density_conversion": "q*mbarv/species_mw*pmid/(kB*T)*1e-6 -> cm^-3",'
      write(118,'(A)') '  "source_species_order": ["O","O2","H","N","NO","N2","He"],'
      write(118,'(A)') '  "payload_species_order": ["H","O","NO","O2","He","N2","N"],'
      write(118,'(A)') '  "source_species_indices": ['
      do ispc = 1, n_live_species
         if (ispc < n_live_species) then
            write(118,'(A,A,A,I0,A)') '    {"name":"', trim(live_species(ispc)), '","index":', live_ind(ispc), '},'
         else
            write(118,'(A,A,A,I0,A)') '    {"name":"', trim(live_species(ispc)), '","index":', live_ind(ispc), '}'
         endif
      enddo
      write(118,'(A)') '  ],'
      write(118,'(A)') '  "fallback_policy": {'
      write(118,'(A)') '    "above_live_top": "payload sample marked invalid so SAMI3 native neutral state is retained",'
      write(118,'(A)') '    "N2": "CAM N2 if finite, otherwise residual closure from major species",'
      write(118,'(A,A,A)') '    "N2_negative_mode": "', trim(n2_negative_mode), '",'
      write(118,'(A)') '    "He": "payload value -1 so SAMI3 native/MSIS He is retained",'
      write(118,'(A)') '    "W": "payload value 0; CAM omega diagnostic only",'
      write(118,'(A)') '    "remap_scaling": "f19 gather-to-root prototype, not f09 production distributed remap"'
      write(118,'(A)') '  },'
      write(118,'(A)') '  "runtime_qc": {'
      write(118,'(A,I0,A)') '    "samples": ', samples, ','
      write(118,'(A,I0,A)') '    "invalid": ', invalid, ','
      write(118,'(A,I0,A)') '    "above_live_top": ', above_top, ','
      write(118,'(A,I0,A)') '    "n2_residual_used": ', n2_used, ','
      write(118,'(A,I0,A)') '    "n2_residual_negative": ', n2_negative, ','
      write(118,'(A,ES24.16,A)') '    "n2_residual_min": ', n2_min, ','
      write(118,'(A,ES24.16)') '    "n2_residual_max": ', n2_max
      write(118,'(A)') '  },'
      write(118,'(A)') '  "sender_checksum": {'
      write(118,'(A)') '    "scope": "sum over all runtime-sent worker payload arrays",'
      write(118,'(A,I0,A)') '    "valid_i": ', valid_i, ','
      write(118,'(A,I0,A)') '    "invalid_i": ', invalid_i, ','
      write(118,'(A,I0,A)') '    "valid_f": ', valid_f, ','
      write(118,'(A,I0,A)') '    "invalid_f": ', invalid_f, ','
      write(118,'(A,ES24.16,A)') '    "sum_denni": ', payload_sums(1), ','
      write(118,'(A,ES24.16,A)') '    "sum_tni": ', payload_sums(2), ','
      write(118,'(A,ES24.16,A)') '    "sum_ui": ', payload_sums(3), ','
      write(118,'(A,ES24.16,A)') '    "sum_vi": ', payload_sums(4), ','
      write(118,'(A,ES24.16,A)') '    "sum_wi": ', payload_sums(5), ','
      write(118,'(A,ES24.16,A)') '    "sum_dennf": ', payload_sums(6), ','
      write(118,'(A,ES24.16,A)') '    "sum_tnf": ', payload_sums(7), ','
      write(118,'(A,ES24.16,A)') '    "sum_uf": ', payload_sums(8), ','
      write(118,'(A,ES24.16,A)') '    "sum_vf": ', payload_sums(9), ','
      write(118,'(A,ES24.16)') '    "sum_wf": ', payload_sums(10)
      write(118,'(A)') '  }'
      write(118,'(A)') '}'
      close(118)

   end subroutine wxsami3_write_live_packet_meta

   subroutine wxsami3_dump_live_state(state, nstep, dtime_phys)

      include 'mpif.h'

      type(physics_state), intent(in) :: state(:)
      integer, intent(in) :: nstep
      real(r8), intent(in) :: dtime_phys

      integer :: ierr, myrank, nprocs
      integer :: live_ind(n_live_species)
      integer :: local_cols, pos
      integer :: lchnk, i, k, ispc, ncol, chunk_id
      integer :: header(12)
      integer, allocatable :: cid(:), lchnk_idx(:), col_idx(:)
      real(r8), allocatable :: lat_deg(:), lon_deg(:), ps(:)
      real(r8), allocatable :: profile(:,:,:), qprof(:,:,:)
      character(len=1024) :: fname

      call MPI_Comm_rank(mpicom, myrank, ierr)
      call MPI_Comm_size(mpicom, nprocs, ierr)
      call wxsami3_get_species_indices(live_ind)

      local_cols = 0
      do lchnk = lbound(state, 1), ubound(state, 1)
         local_cols = local_cols + state(lchnk)%ncol
      enddo

      allocate(cid(local_cols), lchnk_idx(local_cols), col_idx(local_cols))
      allocate(lat_deg(local_cols), lon_deg(local_cols), ps(local_cols))
      allocate(profile(pver, local_cols, n_dump_profile))
      allocate(qprof(pver, local_cols, n_live_species))

      cid = -1
      lchnk_idx = -1
      col_idx = -1
      lat_deg = huge(1._r8)
      lon_deg = huge(1._r8)
      ps = huge(1._r8)
      profile = huge(1._r8)
      qprof = huge(1._r8)

      pos = 0
      do lchnk = lbound(state, 1), ubound(state, 1)
         chunk_id = state(lchnk)%lchnk
         ncol = state(lchnk)%ncol
         do i = 1, ncol
            pos = pos + 1
            lchnk_idx(pos) = chunk_id
            col_idx(pos) = i
            if (allocated(state(lchnk)%cid)) cid(pos) = state(lchnk)%cid(i)
            if (allocated(state(lchnk)%lat)) lat_deg(pos) = state(lchnk)%lat(i) * rad_to_deg
            if (allocated(state(lchnk)%lon)) lon_deg(pos) = state(lchnk)%lon(i) * rad_to_deg
            if (allocated(state(lchnk)%ps)) ps(pos) = state(lchnk)%ps(i)
            do k = 1, pver
               profile(k,pos,1) = state(lchnk)%t(i,k)
               profile(k,pos,2) = state(lchnk)%u(i,k)
               profile(k,pos,3) = state(lchnk)%v(i,k)
               profile(k,pos,4) = state(lchnk)%omega(i,k)
               profile(k,pos,5) = state(lchnk)%pmid(i,k)
               profile(k,pos,6) = state(lchnk)%zm(i,k)
               if (allocated(mbarv)) profile(k,pos,7) = mbarv(i,k,chunk_id)
               do ispc = 1, n_live_species
                  if (live_ind(ispc) > 0) qprof(k,pos,ispc) = state(lchnk)%q(i,k,live_ind(ispc))
               enddo
            enddo
         enddo
      enddo

      header(1) = live_dump_magic
      header(2) = 1
      header(3) = nstep
      header(4) = packet_count
      header(5) = myrank
      header(6) = nprocs
      header(7) = pver
      header(8) = n_live_species
      header(9) = n_dump_profile
      header(10) = local_cols
      header(11) = merge(1, 0, allocated(mbarv))
      header(12) = 1

      write(fname,'(A,"rank",I4.4,"_pkt",I6.6,".bin")') trim(live_dump_prefix), myrank, packet_count
      open(unit=121, file=trim(fname), form='unformatted', access='stream', &
           convert='little_endian', status='replace', action='write', iostat=ierr)
      if (ierr /= 0) then
         write(iulog,*) 'WXSAMI3 warning: failed to open live dump file: ', trim(fname)
      else
         write(121) header
         write(121) dtime_phys
         write(121) live_ind
         write(121) cid
         write(121) lchnk_idx
         write(121) col_idx
         write(121) lat_deg
         write(121) lon_deg
         write(121) ps
         write(121) profile
         write(121) qprof
         close(121)
      endif

      if (masterproc .and. .not. live_dump_meta_written) then
         call wxsami3_write_live_dump_meta()
         live_dump_meta_written = .true.
      endif
      if (masterproc) write(iulog,*) 'WXSAMI3 live state dump packet written: ', packet_count

      deallocate(cid, lchnk_idx, col_idx, lat_deg, lon_deg, ps, profile, qprof)

   end subroutine wxsami3_dump_live_state

   subroutine wxsami3_write_live_dump_meta()

      integer :: ios, ispc
      character(len=1024) :: fname

      write(fname,'(A,"meta.json")') trim(live_dump_prefix)
      open(unit=122, file=trim(fname), status='replace', action='write', iostat=ios)
      if (ios /= 0) then
         write(iulog,*) 'WXSAMI3 warning: failed to write live dump metadata: ', trim(fname)
         return
      endif

      write(122,'(A)') '{'
      write(122,'(A)') '  "format": "wxsami3-live-phys-state-snapshot",'
      write(122,'(A,I0,A)') '  "version": ', 1, ','
      write(122,'(A,I0,A)') '  "magic": ', live_dump_magic, ','
      write(122,'(A)') '  "endianness": "little_endian",'
      write(122,'(A)') '  "integer_kind": "Fortran default integer",'
      write(122,'(A)') '  "real_kind": "SHR_KIND_R8",'
      if (live_payload_mode) then
         write(122,'(A)') '  "transport_status": "diagnostic snapshot plus runtime live payload sent",'
      else
         write(122,'(A)') '  "transport_status": "diagnostic snapshot only; file-backed payload sent",'
      endif
      write(122,'(A)') '  "record_order": ["header_i4_12", "dtime_phys_r8", ' // &
                         '"species_indices_i4", "cid_i4", "lchnk_i4", "col_i4", ' // &
                         '"lat_deg_r8", "lon_deg_r8", "state_ps_pa_r8", ' // &
                         '"profile_r8", "qprof_r8"],'
      write(122,'(A)') '  "profile_order": ["T_K", "U_m_s", "V_m_s", "OMEGA_Pa_s", "PMID_Pa", "ZM_m", "MBARV_kg_mol"],'
      write(122,'(A)') '  "state_ps_note": "raw physics_state%ps snapshot; SAMI3 payload uses profile PMID_Pa",'
      write(122,'(A)') '  "q_unit": "mass_mixing_ratio",'
      write(122,'(A)') '  "density_conversion": "q*mbarv/species_mw*pmid/(kB*T)*1e-6 -> cm^-3",'
      write(122,'(A)') '  "species": ['
      do ispc = 1, n_live_species
         if (ispc < n_live_species) then
            write(122,'(A,A,A,ES12.4,A)') '    {"name":"', trim(live_species(ispc)), '","mw":', live_species_mw(ispc), '},'
         else
            write(122,'(A,A,A,ES12.4,A)') '    {"name":"', trim(live_species(ispc)), '","mw":', live_species_mw(ispc), '}'
         endif
      enddo
      write(122,'(A)') '  ]'
      write(122,'(A)') '}'
      close(122)

   end subroutine wxsami3_write_live_dump_meta

   subroutine wxsami3_load_live_map()

      integer :: ios
      integer :: header(8)

      if (live_map_loaded) return
      if (.not. masterproc) return

      open(unit=123, file=trim(live_map_file), form='unformatted', access='stream', &
           convert='little_endian', status='old', action='read', iostat=ios)
      if (ios /= 0) call endrun('WXSAMI3 failed to open live runtime map file')

      read(123) header
      if (header(1) /= live_map_magic .or. header(2) /= 1 .or. &
          header(3) /= sami_nz .or. header(4) /= sami_nf .or. &
          header(5) /= sami_nlt) then
         write(iulog,*) 'WXSAMI3 live map header=', header
         call endrun('WXSAMI3 live runtime map header mismatch')
      endif

      live_map_npoints = header(6)
      live_map_ns = header(7)
      live_map_nsource = header(8)
      if (live_map_npoints /= sami_nz*sami_nf*sami_nlt) then
         call endrun('WXSAMI3 live runtime map npoints mismatch')
      endif

      allocate(live_map_zalt(live_map_npoints))
      allocate(live_map_row_start(live_map_npoints), live_map_row_count(live_map_npoints))
      allocate(live_map_col(live_map_ns), live_map_s(live_map_ns))

      read(123) live_map_zalt
      read(123) live_map_row_start
      read(123) live_map_row_count
      read(123) live_map_col
      read(123) live_map_s
      close(123)

      live_map_loaded = .true.
      write(iulog,*) 'WXSAMI3 live runtime map loaded: npoints,n_s,nsource=', &
                     live_map_npoints, live_map_ns, live_map_nsource

   end subroutine wxsami3_load_live_map

   subroutine wxsami3_send_live_packet(nstep, dtime_phys, packet_hour, state)

      include 'mpif.h'

      integer, intent(in) :: nstep
      real(r8), intent(in) :: dtime_phys
      real, intent(in) :: packet_hour
      type(physics_state), intent(in) :: state(:)

      integer :: ierr, myrank, nprocs
      integer :: live_ind(n_live_species)
      integer :: lchnk, i, k, ispc, ncol, chunk_id, pos
      integer :: local_cols, max_cols, local_dcount
      integer :: total_cols, total_data
      integer :: m, f, cid, offset, present_count
      integer, allocatable :: counts(:), displs(:), dcounts(:), ddispls(:)
      integer, allocatable :: local_cid(:), recv_cid(:)
      real(r8), allocatable :: local_data(:,:,:), recv_data(:), src(:,:,:)
      logical, allocatable :: present(:)
      integer :: worker
      real, allocatable :: denni(:), tni(:), ui(:), vi(:), wi(:)
      real, allocatable :: dennf(:), tnf(:), uf(:), vf(:), wf(:)
      integer :: samples, invalid, above_top, n2_used, n2_negative
      integer :: valid_i, invalid_i, valid_f, invalid_f
      real(r8) :: payload_sums(10)
      real(r8) :: n2_min, n2_max

      call MPI_Comm_rank(mpicom, myrank, ierr)
      call MPI_Comm_size(mpicom, nprocs, ierr)
      call wxsami3_get_species_indices(live_ind)

      if (.not. allocated(mbarv)) call endrun('WXSAMI3 live mode requires allocated CAM mbarv')

      local_cols = 0
      do lchnk = lbound(state, 1), ubound(state, 1)
         local_cols = local_cols + state(lchnk)%ncol
      enddo
      max_cols = max(1, local_cols)
      allocate(local_cid(max_cols))
      allocate(local_data(pver, n_live_fields, max_cols))
      local_cid = -1
      local_data = huge(1._r8)

      pos = 0
      do lchnk = lbound(state, 1), ubound(state, 1)
         chunk_id = state(lchnk)%lchnk
         ncol = state(lchnk)%ncol
         if (.not. allocated(state(lchnk)%cid)) then
            call endrun('WXSAMI3 live mode requires CAM cid in physics_state')
         endif
         do i = 1, ncol
            pos = pos + 1
            local_cid(pos) = state(lchnk)%cid(i)
            do k = 1, pver
               local_data(k,1,pos) = state(lchnk)%t(i,k)
               local_data(k,2,pos) = state(lchnk)%u(i,k)
               local_data(k,3,pos) = state(lchnk)%v(i,k)
               local_data(k,4,pos) = state(lchnk)%pmid(i,k)
               local_data(k,5,pos) = state(lchnk)%zm(i,k)
               local_data(k,6,pos) = mbarv(i,k,chunk_id)
               do ispc = 1, 6
                  if (live_ind(ispc) > 0) local_data(k,6+ispc,pos) = state(lchnk)%q(i,k,live_ind(ispc))
               enddo
            enddo
         enddo
      enddo

      allocate(counts(nprocs), displs(nprocs), dcounts(nprocs), ddispls(nprocs))
      counts = 0
      displs = 0
      dcounts = 0
      ddispls = 0
      call MPI_Gather(local_cols, 1, MPI_INTEGER, counts, 1, MPI_INTEGER, 0, mpicom, ierr)

      total_cols = 0
      total_data = 0
      if (masterproc) then
         do i = 1, nprocs
            displs(i) = total_cols
            ddispls(i) = total_data
            dcounts(i) = counts(i) * pver * n_live_fields
            total_cols = total_cols + counts(i)
            total_data = total_data + dcounts(i)
         enddo
         call wxsami3_load_live_map()
         allocate(recv_cid(max(1,total_cols)))
         allocate(recv_data(max(1,total_data)))
      else
         allocate(recv_cid(1))
         allocate(recv_data(1))
      endif

      local_dcount = local_cols * pver * n_live_fields
      call MPI_Gatherv(local_cid, local_cols, MPI_INTEGER, recv_cid, counts, displs, &
                       MPI_INTEGER, 0, mpicom, ierr)
      call MPI_Gatherv(local_data, local_dcount, MPI_DOUBLE_PRECISION, recv_data, &
                       dcounts, ddispls, MPI_DOUBLE_PRECISION, 0, mpicom, ierr)

      deallocate(local_cid, local_data, counts, displs, dcounts, ddispls)

      if (masterproc) then
         allocate(src(pver, live_map_nsource, n_live_fields))
         allocate(present(live_map_nsource))
         src = huge(1._r8)
         present = .false.
         do m = 1, total_cols
            cid = recv_cid(m)
            if (cid < 1 .or. cid > live_map_nsource) then
               write(iulog,*) 'WXSAMI3 live bad cid,total_cols=', cid, total_cols
               call endrun('WXSAMI3 live cid out of source range')
            endif
            present(cid) = .true.
            offset = (m - 1) * pver * n_live_fields
            do f = 1, n_live_fields
               do k = 1, pver
                  src(k,cid,f) = recv_data(offset + (f - 1) * pver + k)
               enddo
            enddo
         enddo
         present_count = count(present)
         if (present_count /= live_map_nsource) then
            write(iulog,*) 'WXSAMI3 live source coverage present,expected=', &
                           present_count, live_map_nsource
            call endrun('WXSAMI3 live source coverage incomplete')
         endif

         samples = 0
         invalid = 0
         above_top = 0
         n2_used = 0
         n2_negative = 0
         n2_min = huge(1._r8)
         n2_max = -huge(1._r8)
         valid_i = 0
         invalid_i = 0
         valid_f = 0
         invalid_f = 0
         payload_sums = 0._r8

         do worker = 1, num_workers
            allocate(denni(sami_nlocal4), tni(sami_nlocal), ui(sami_nlocal), &
                     vi(sami_nlocal), wi(sami_nlocal))
            allocate(dennf(sami_nlocal4), tnf(sami_nlocal), uf(sami_nlocal), &
                     vf(sami_nlocal), wf(sami_nlocal))
            call wxsami3_fill_live_worker(worker, src, denni, tni, ui, vi, wi, &
                                          samples, invalid, above_top, n2_used, &
                                          n2_negative, n2_min, n2_max)
            dennf = denni
            tnf = tni
            uf = ui
            vf = vi
            wf = wi
            call wxsami3_accum_payload_qc(denni, tni, ui, vi, wi, dennf, tnf, &
                                          uf, vf, wf, valid_i, invalid_i, &
                                          valid_f, invalid_f, payload_sums)
            call wxsami3_send_worker_arrays(worker, nstep, packet_hour, denni, tni, &
                                            ui, vi, wi, dennf, tnf, uf, vf, wf)
            deallocate(denni, tni, ui, vi, wi, dennf, tnf, uf, vf, wf)
         enddo

         write(iulog,*) 'WXSAMI3 live runtime packet QC samples,invalid,above_top=', &
                        samples, invalid, above_top
         write(iulog,*) 'WXSAMI3 live runtime N2 residual used,negative,min,max=', &
                        n2_used, n2_negative, n2_min, n2_max
         write(iulog,*) 'WXSAMI3 sent live neutral packet: nstep,packet_hour,count=', &
                        nstep, packet_hour, packet_count
         if (len_trim(meta_file) > 0) then
            call wxsami3_write_live_packet_meta(nstep, dtime_phys, packet_hour, live_ind, &
                                                samples, invalid, above_top, n2_used, &
                                                n2_negative, n2_min, n2_max, valid_i, &
                                                invalid_i, valid_f, invalid_f, payload_sums)
         endif
         deallocate(src, present)
      endif

      deallocate(recv_cid, recv_data)

   end subroutine wxsami3_send_live_packet

   subroutine wxsami3_accum_payload_qc(denni, tni, ui, vi, wi, dennf, tnf, uf, vf, wf, &
                                       valid_i, invalid_i, valid_f, invalid_f, payload_sums)

      real, intent(in) :: denni(:), tni(:), ui(:), vi(:), wi(:)
      real, intent(in) :: dennf(:), tnf(:), uf(:), vf(:), wf(:)
      integer, intent(inout) :: valid_i, invalid_i, valid_f, invalid_f
      real(r8), intent(inout) :: payload_sums(10)

      valid_i = valid_i + count(denni(1:sami_nlocal) >= 0.0)
      invalid_i = invalid_i + count(denni(1:sami_nlocal) < 0.0)
      valid_f = valid_f + count(dennf(1:sami_nlocal) >= 0.0)
      invalid_f = invalid_f + count(dennf(1:sami_nlocal) < 0.0)

      payload_sums(1) = payload_sums(1) + sum(real(denni, kind=r8))
      payload_sums(2) = payload_sums(2) + sum(real(tni, kind=r8))
      payload_sums(3) = payload_sums(3) + sum(real(ui, kind=r8))
      payload_sums(4) = payload_sums(4) + sum(real(vi, kind=r8))
      payload_sums(5) = payload_sums(5) + sum(real(wi, kind=r8))
      payload_sums(6) = payload_sums(6) + sum(real(dennf, kind=r8))
      payload_sums(7) = payload_sums(7) + sum(real(tnf, kind=r8))
      payload_sums(8) = payload_sums(8) + sum(real(uf, kind=r8))
      payload_sums(9) = payload_sums(9) + sum(real(vf, kind=r8))
      payload_sums(10) = payload_sums(10) + sum(real(wf, kind=r8))

   end subroutine wxsami3_accum_payload_qc

   subroutine wxsami3_fill_live_worker(worker, src, den, tn, uu, vv, ww, &
                                       samples, invalid, above_top, n2_used, &
                                       n2_negative, n2_min, n2_max)

      integer, intent(in) :: worker
      real(r8), intent(in) :: src(:,:,:)
      real, intent(out) :: den(:), tn(:), uu(:), vv(:), ww(:)
      integer, intent(inout) :: samples, invalid, above_top, n2_used, n2_negative
      real(r8), intent(inout) :: n2_min, n2_max

      integer :: i, j, k, n, g0, target_idx, lidx, didx
      real :: dvals(sami_nneut), tval, uval, vval, wval
      logical :: is_invalid, is_above
      real(r8) :: n2_residual

      den = -1.0
      tn = -1.0
      uu = 0.0
      vv = 0.0
      ww = 0.0

      do k = 1, sami_nl
         g0 = (worker - 1) * (sami_nl - 2) + (k - 2)
         do while (g0 < 0)
            g0 = g0 + sami_nlt
         enddo
         do while (g0 >= sami_nlt)
            g0 = g0 - sami_nlt
         enddo
         do j = 1, sami_nf
            do i = 1, sami_nz
               target_idx = (g0 * sami_nf + (j - 1)) * sami_nz + i
               lidx = ((k - 1) * sami_nf + (j - 1)) * sami_nz + i
               call wxsami3_sample_live_point(src, target_idx, dvals, tval, uval, &
                                              vval, wval, is_invalid, is_above, &
                                              n2_residual)
               samples = samples + 1
               if (is_invalid) invalid = invalid + 1
               if (is_above) above_top = above_top + 1
               if (wxsami3_valid_r8(n2_residual)) then
                  n2_used = n2_used + 1
                  n2_min = min(n2_min, n2_residual)
                  n2_max = max(n2_max, n2_residual)
                  if (n2_residual < 0._r8) n2_negative = n2_negative + 1
               endif
               tn(lidx) = tval
               uu(lidx) = uval
               vv(lidx) = vval
               ww(lidx) = wval
               do n = 1, sami_nneut
                  didx = (((n - 1) * sami_nl + (k - 1)) * sami_nf + (j - 1)) * sami_nz + i
                  den(didx) = dvals(n)
               enddo
            enddo
         enddo
      enddo

   end subroutine wxsami3_fill_live_worker

   subroutine wxsami3_sample_live_point(src, target_idx, den, tn, uu, vv, ww, &
                                        is_invalid, is_above, n2_residual)

      real(r8), intent(in) :: src(:,:,:)
      integer, intent(in) :: target_idx
      real, intent(out) :: den(sami_nneut), tn, uu, vv, ww
      logical, intent(out) :: is_invalid, is_above
      real(r8), intent(out) :: n2_residual

      integer :: lev, l0, l1, lmin
      real(r8) :: target_alt_m, z, z0, z1, zmin, zmax, best, dist, wgt
      real(r8) :: temp, u_m, v_m, pmid, mbar
      real(r8) :: q_o, q_o2, q_h, q_n, q_no, q_n2
      logical :: bracketed

      call wxsami3_mark_invalid(den, tn, uu, vv, ww)
      is_invalid = .true.
      is_above = .false.
      n2_residual = huge(1._r8)

      target_alt_m = real(live_map_zalt(target_idx), r8) * 1000._r8
      zmin = huge(1._r8)
      zmax = -huge(1._r8)
      best = huge(1._r8)
      l0 = 1
      l1 = 1
      lmin = 1
      wgt = 0._r8
      bracketed = .false.

      do lev = 1, pver
         z = wxsami3_weighted_live(src, target_idx, lev, 5)
         if (.not. wxsami3_valid_r8(z)) return
         dist = abs(z - target_alt_m)
         if (dist < best) then
            best = dist
            l0 = lev
            l1 = lev
         endif
         if (z > zmax) zmax = z
         if (z < zmin) then
            zmin = z
            lmin = lev
         endif
      enddo

      do lev = 1, pver - 1
         z0 = wxsami3_weighted_live(src, target_idx, lev, 5)
         z1 = wxsami3_weighted_live(src, target_idx, lev + 1, 5)
         if (target_alt_m >= min(z0,z1) .and. target_alt_m <= max(z0,z1)) then
            l0 = lev
            l1 = lev + 1
            if (abs(z1 - z0) > 1.0e-9_r8) then
               wgt = (target_alt_m - z0) / (z1 - z0)
            else
               wgt = 0._r8
            endif
            wgt = max(0._r8, min(1._r8, wgt))
            bracketed = .true.
            exit
         endif
      enddo

      if (.not. bracketed .and. target_alt_m > zmax) then
         is_above = .true.
         return
      else if (.not. bracketed .and. target_alt_m < zmin) then
         l0 = lmin
         l1 = lmin
         wgt = 0._r8
      endif

      temp = wxsami3_interp_live(src, target_idx, l0, l1, wgt, 1)
      u_m  = wxsami3_interp_live(src, target_idx, l0, l1, wgt, 2)
      v_m  = wxsami3_interp_live(src, target_idx, l0, l1, wgt, 3)
      pmid = wxsami3_interp_live(src, target_idx, l0, l1, wgt, 4)
      mbar = wxsami3_interp_live(src, target_idx, l0, l1, wgt, 6)
      q_o  = wxsami3_interp_live(src, target_idx, l0, l1, wgt, 7)
      q_o2 = wxsami3_interp_live(src, target_idx, l0, l1, wgt, 8)
      q_h  = wxsami3_interp_live(src, target_idx, l0, l1, wgt, 9)
      q_n  = wxsami3_interp_live(src, target_idx, l0, l1, wgt, 10)
      q_no = wxsami3_interp_live(src, target_idx, l0, l1, wgt, 11)
      q_n2 = wxsami3_interp_live(src, target_idx, l0, l1, wgt, 12)

      if (wxsami3_valid_r8(q_o))  q_o  = max(q_o,  0._r8)
      if (wxsami3_valid_r8(q_o2)) q_o2 = max(q_o2, 0._r8)
      if (wxsami3_valid_r8(q_h))  q_h  = max(q_h,  0._r8)
      if (wxsami3_valid_r8(q_n))  q_n  = max(q_n,  0._r8)
      if (wxsami3_valid_r8(q_no)) q_no = max(q_no, 0._r8)
      if (wxsami3_valid_r8(q_n2)) q_n2 = max(q_n2, 0._r8)

      if (.not. wxsami3_valid_r8(q_n2) .and. wxsami3_valid_r8(q_h) .and. &
          wxsami3_valid_r8(q_o) .and. wxsami3_valid_r8(q_o2) .and. &
          wxsami3_valid_r8(q_n) .and. wxsami3_valid_r8(q_no)) then
         n2_residual = 1._r8 - q_h - q_o - q_o2 - q_n - q_no
         if (n2_residual < 0._r8) then
            select case (trim(n2_negative_mode))
            case ('invalid', 'INVALID')
               return
            case ('fail', 'FAIL')
               call endrun('WXSAMI3 residual N2 is negative')
            case default
               q_n2 = 1.0e-20_r8
            end select
         else
            q_n2 = max(n2_residual, 1.0e-20_r8)
         endif
      endif

      if (.not. wxsami3_valid_r8(temp) .or. .not. wxsami3_valid_r8(u_m) .or. &
          .not. wxsami3_valid_r8(v_m) .or. .not. wxsami3_valid_r8(pmid) .or. &
          .not. wxsami3_valid_r8(mbar) .or. .not. wxsami3_valid_r8(q_h) .or. &
          .not. wxsami3_valid_r8(q_o) .or. .not. wxsami3_valid_r8(q_o2) .or. &
          .not. wxsami3_valid_r8(q_n) .or. .not. wxsami3_valid_r8(q_no) .or. &
          .not. wxsami3_valid_r8(q_n2)) return

      temp = max(temp, 50._r8)
      den(1) = real(wxsami3_density_cm3(q_h,  mbar, pmid, temp, 1._r8))
      den(2) = real(wxsami3_density_cm3(q_o,  mbar, pmid, temp, 16._r8))
      den(3) = real(wxsami3_density_cm3(q_no, mbar, pmid, temp, 30._r8))
      den(4) = real(wxsami3_density_cm3(q_o2, mbar, pmid, temp, 32._r8))
      den(5) = -1.0
      den(6) = real(wxsami3_density_cm3(q_n2, mbar, pmid, temp, 28._r8))
      den(7) = real(wxsami3_density_cm3(q_n,  mbar, pmid, temp, 14._r8))

      tn = real(temp)
      uu = real(100._r8 * u_m)
      vv = real(100._r8 * v_m)
      ww = 0.0
      is_invalid = .false.

   end subroutine wxsami3_sample_live_point

   function wxsami3_weighted_live(src, target_idx, lev, field_id) result(value)

      real(r8), intent(in) :: src(:,:,:)
      integer, intent(in) :: target_idx, lev, field_id
      real(r8) :: value

      integer :: start, count, q, idx, col
      real(r8) :: sumv, sumw, v

      value = huge(1._r8)
      start = live_map_row_start(target_idx)
      count = live_map_row_count(target_idx)
      if (start <= 0 .or. count <= 0) return
      sumv = 0._r8
      sumw = 0._r8
      do q = 0, count - 1
         idx = start + q
         col = live_map_col(idx)
         if (col < 1 .or. col > size(src,2)) return
         v = src(lev,col,field_id)
         if (.not. wxsami3_valid_r8(v)) return
         sumv = sumv + live_map_s(idx) * v
         sumw = sumw + live_map_s(idx)
      enddo
      if (sumw > 0._r8) value = sumv / sumw

   end function wxsami3_weighted_live

   function wxsami3_interp_live(src, target_idx, l0, l1, wgt, field_id) result(value)

      real(r8), intent(in) :: src(:,:,:)
      integer, intent(in) :: target_idx, l0, l1, field_id
      real(r8), intent(in) :: wgt
      real(r8) :: value
      real(r8) :: a, b

      value = huge(1._r8)
      a = wxsami3_weighted_live(src, target_idx, l0, field_id)
      b = wxsami3_weighted_live(src, target_idx, l1, field_id)
      if (.not. wxsami3_valid_r8(a) .or. .not. wxsami3_valid_r8(b)) return
      value = (1._r8 - wgt) * a + wgt * b

   end function wxsami3_interp_live

   function wxsami3_density_cm3(qmix, mbar, pmid, temp, species_mw) result(value)

      real(r8), intent(in) :: qmix, mbar, pmid, temp, species_mw
      real(r8) :: value

      value = huge(1._r8)
      if (.not. wxsami3_valid_r8(qmix) .or. .not. wxsami3_valid_r8(mbar) .or. &
          .not. wxsami3_valid_r8(pmid) .or. .not. wxsami3_valid_r8(temp)) return
      if (temp <= 0._r8 .or. pmid <= 0._r8 .or. mbar <= 0._r8) return
      value = max(qmix * mbar / species_mw * pmid / (kb_si * temp) * 1.0e-6_r8, &
                  1.0e-30_r8)

   end function wxsami3_density_cm3

   subroutine wxsami3_mark_invalid(den, tn, uu, vv, ww)

      real, intent(out) :: den(sami_nneut), tn, uu, vv, ww

      den = -1.0
      tn = -1.0
      uu = 0.0
      vv = 0.0
      ww = 0.0

   end subroutine wxsami3_mark_invalid

   logical function wxsami3_valid_r8(value)

      real(r8), intent(in) :: value

      wxsami3_valid_r8 = value == value .and. abs(value) < huge(1._r8) * 0.5_r8

   end function wxsami3_valid_r8

   subroutine wxsami3_send_worker_arrays(worker, nstep, packet_hour, denni, tni, &
                                         ui, vi, wi, dennf, tnf, uf, vf, wf)

      include 'mpif.h'

      integer, intent(in) :: worker, nstep
      real, intent(in) :: packet_hour
      real, intent(in) :: denni(:), tni(:), ui(:), vi(:), wi(:)
      real, intent(in) :: dennf(:), tnf(:), uf(:), vf(:), wf(:)
      integer :: ios
      integer :: header(6)

      header(1) = payload_magic
      header(2) = sami_nz
      header(3) = sami_nf
      header(4) = sami_nl
      header(5) = sami_nneut
      header(6) = nstep

      call MPI_Send(header, 6, MPI_INTEGER, worker, tag_header, peer_comm, ios)
      call MPI_Send(packet_hour, 1, MPI_REAL, worker, tag_hr, peer_comm, ios)
      call MPI_Send(denni, sami_nlocal4, MPI_REAL, worker, tag_denni, peer_comm, ios)
      call MPI_Send(tni, sami_nlocal, MPI_REAL, worker, tag_tni, peer_comm, ios)
      call MPI_Send(ui, sami_nlocal, MPI_REAL, worker, tag_ui, peer_comm, ios)
      call MPI_Send(vi, sami_nlocal, MPI_REAL, worker, tag_vi, peer_comm, ios)
      call MPI_Send(wi, sami_nlocal, MPI_REAL, worker, tag_wi, peer_comm, ios)
      call MPI_Send(dennf, sami_nlocal4, MPI_REAL, worker, tag_dennf, peer_comm, ios)
      call MPI_Send(tnf, sami_nlocal, MPI_REAL, worker, tag_tnf, peer_comm, ios)
      call MPI_Send(uf, sami_nlocal, MPI_REAL, worker, tag_uf, peer_comm, ios)
      call MPI_Send(vf, sami_nlocal, MPI_REAL, worker, tag_vf, peer_comm, ios)
      call MPI_Send(wf, sami_nlocal, MPI_REAL, worker, tag_wf, peer_comm, ios)

   end subroutine wxsami3_send_worker_arrays

   subroutine wxsami3_cam_finalize()

      include 'mpif.h'

      integer :: ierr, stat, lenval
      integer :: worker, done_value
      character(len=16) :: value

      if (.not. is_connected) return

      if (masterproc) then
         done_value = packet_count
         do worker = 0, num_workers
            call MPI_Send(done_value, 1, MPI_INTEGER, worker, tag_done, peer_comm, ierr)
            if (ierr /= MPI_SUCCESS) call endrun('WXSAMI3 MPI_Send done signal failed')
         enddo
         write(iulog,*) 'WXSAMI3 sent done signal to SAMI3'
      endif

      value = ''
      call get_environment_variable('WXSAMI3_SKIP_DISCONNECT', value, length=lenval, status=stat)
      if (stat == 0 .and. lenval > 0 .and. trim(value) == '1') then
         is_connected = .false.
         is_enabled = .false.
         if (masterproc) write(iulog,*) 'WXSAMI3 disconnect skipped'
         return
      endif
      call MPI_Comm_disconnect(peer_comm, ierr)
      is_connected = .false.
      is_enabled = .false.
      if (masterproc) write(iulog,*) 'WXSAMI3 disconnected from SAMI3'

   end subroutine wxsami3_cam_finalize

   subroutine wxsami3_send_worker(worker, nstep, packet_hour)

      include 'mpif.h'

      integer, intent(in) :: worker
      integer, intent(in) :: nstep
      real, intent(in) :: packet_hour

      integer :: ios
      integer :: file_header(5)
      integer :: header(6)
      integer :: nz_s, nf_s, nl_s, nneut_s
      integer :: nlocal, nlocal4
      character(len=1024) :: fname
      real, allocatable :: denni(:), tni(:), ui(:), vi(:), wi(:)
      real, allocatable :: dennf(:), tnf(:), uf(:), vf(:), wf(:)

      write(fname,'(A,I4.4,A)') trim(payload_prefix), worker, '.bin'
      open(unit=120, file=trim(fname), form='unformatted', access='stream', &
           convert='little_endian', status='old', action='read', iostat=ios)
      if (ios /= 0) call endrun('WXSAMI3 failed to open payload file')

      read(120) file_header
      nz_s = file_header(2)
      nf_s = file_header(3)
      nl_s = file_header(4)
      nneut_s = file_header(5)
      nlocal = nz_s * nf_s * nl_s
      nlocal4 = nlocal * nneut_s

      allocate(denni(nlocal4), tni(nlocal), ui(nlocal), vi(nlocal), wi(nlocal))
      allocate(dennf(nlocal4), tnf(nlocal), uf(nlocal), vf(nlocal), wf(nlocal))

      read(120) denni
      read(120) tni
      read(120) ui
      read(120) vi
      read(120) wi
      read(120) dennf
      read(120) tnf
      read(120) uf
      read(120) vf
      read(120) wf
      close(120)

      header(1:5) = file_header
      header(6) = nstep

      call MPI_Send(header, 6, MPI_INTEGER, worker, tag_header, peer_comm, ios)
      call MPI_Send(packet_hour, 1, MPI_REAL, worker, tag_hr, peer_comm, ios)
      call MPI_Send(denni, nlocal4, MPI_REAL, worker, tag_denni, peer_comm, ios)
      call MPI_Send(tni, nlocal, MPI_REAL, worker, tag_tni, peer_comm, ios)
      call MPI_Send(ui, nlocal, MPI_REAL, worker, tag_ui, peer_comm, ios)
      call MPI_Send(vi, nlocal, MPI_REAL, worker, tag_vi, peer_comm, ios)
      call MPI_Send(wi, nlocal, MPI_REAL, worker, tag_wi, peer_comm, ios)
      call MPI_Send(dennf, nlocal4, MPI_REAL, worker, tag_dennf, peer_comm, ios)
      call MPI_Send(tnf, nlocal, MPI_REAL, worker, tag_tnf, peer_comm, ios)
      call MPI_Send(uf, nlocal, MPI_REAL, worker, tag_uf, peer_comm, ios)
      call MPI_Send(vf, nlocal, MPI_REAL, worker, tag_vf, peer_comm, ios)
      call MPI_Send(wf, nlocal, MPI_REAL, worker, tag_wf, peer_comm, ios)

      deallocate(denni, tni, ui, vi, wi, dennf, tnf, uf, vf, wf)

   end subroutine wxsami3_send_worker

end module wxsami3_online_stub_mod
