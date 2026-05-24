OBJ	= \
	parameter_mod.o\
	parameter_apex_mod.o\
	namelist_mod.o\
	variable_mod.o\
	message_passing_mod.o\
	grid_mod.o\
	waccmx_neutral_mod.o\
	chemistry_mod.o\
	time_mod.o\
	atomic_mod.o\
	conductance_mod.o\
	exb_mod.o\
	hardy_mod.o\
	misc_mod.o\
	photo_production_mod_drob.o\
	msis2.o\
	gtd8d.o\
	grid3-3.22.o\
	hwm93.o\
	madala_sevp_dp.o\
	sami3-3.22.o\
	sevp13_dp.o\
	hwm14.o\
	heating.o\
	solvers.o\
	photo_production.o\
	output.o\
	chemistry.o\
	potential.o\
	exb_transport.o\
	misc.o\
	neutral.o\
	shutdown.o\
	hardy_sami3.o\
	weimer_omni.o\
	weimer_grid.o\
	weimer_phi.o\
	apexsh.o\
	magfld.o\
	nrlmsise00.o

# gfortran

#f90  = mpif90 -O2 -fno-automatic  -mcmodel=large 
#f77  = gfortran -fno-automatic  -mcmodel=large  -O2

# debug

#f90 = mpif90 -fno-automatic -g -fcheck=all -Wall -mcmodel=large 
#f77 = gfortran -fno-automatic -g -fcheck=all -Wall -mcmodel=large 

# intel ifort

  f90 = mpif90 -O2 -fno-automatic -mcmodel=large
  f77 = gfortran -O2 -fno-automatic -mcmodel=large

# debug

#  f90 = mpif90 -save -C -traceback -shared-intel -vec_report0
#  f77 = ifort  -save -C -traceback -shared-intel -vec_report0

.SUFFIXES : .o .f90 .f .F90 .F


%.o:%.mod

.f.o:
	$(f77) -c $*.f 

.f90.o:
	$(f90) -c $*.f90

.F90.o:
	$(f90) -c $*.F90

.F.o:
	$(f90) -c $*.F

clean:
	rm *.o *.x *.mod

sami3.x:	$(OBJ)
	$(f90) -o sami3.x $(OBJ)

#$(OBJ): com3_mpi-2.00.inc
#$(OBJ): param3_mpi-2.00.inc
