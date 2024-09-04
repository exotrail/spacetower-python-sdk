def add_grid(axis):
    axis.grid()
    axis.minorticks_on()
    axis.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.5)
    axis.grid(which='minor', linestyle=':', linewidth='0.5', color='gray', alpha=0.5)
