#!/usr/bin/env python

from   astropy.io import fits
import numpy      as np
import os
import optparse
import warnings
warnings.filterwarnings('ignore')
from matplotlib.tri import Triangulation, TriAnalyzer

#import matplotlib
#matplotlib.use('pdf')
#
import matplotlib.pyplot       as     plt
from   mpl_toolkits.axes_grid1 import AxesGrid
from   matplotlib.ticker       import MultipleLocator, FuncFormatter

from plotbin.sauron_colormap import register_sauron_colormap
register_sauron_colormap()

# Make plotting routine python 2 and 3 compatible
try:
    input = raw_input
except NameError:
    pass


"""
PURPOSE:
  Plot maps of the emission-line analysis. 
  
  Note that this routine will be executed automatically during runtime of the
  pipeline, but can also be run independently of the pipeline. 
"""


def TicklabelFormatter(x, pos):
    return( "${}$".format(int(x)).replace("-", r"\textendash") )

def setup_plot(usetex=False):

    fontsize = 18
    dpi = 300
    
    plt.rc('font', family='serif')
    plt.rc('text', usetex=usetex)
    
    plt.rcParams['axes.labelsize'] = fontsize
    plt.rcParams['legend.fontsize'] = fontsize-3
    plt.rcParams['legend.fancybox'] = True
    plt.rcParams['font.size'] = fontsize
    
    plt.rcParams['xtick.major.pad'] = '7'
    plt.rcParams['ytick.major.pad'] = '7'
    
    plt.rcParams['savefig.bbox'] = 'tight'
    plt.rcParams['savefig.dpi'] = dpi
    plt.rcParams['savefig.pad_inches'] = 0.3
    
    plt.rcParams['text.latex.preamble'] = [r'\boldmath']


def plot_line(LEVEL, FROM_PIPELINE, gandalf_Vel, gandalf_Sigma, gandalf_Flux, gandalf_Ampl, INTERACTIVE, SAVE_AFTER_INTERACTIVE,\
        runname, AoNThreshold, line_idx, lineIdentifier, vminmax, contour_offset_saved, X, Y, FLUX, pixelsize, outdir, rootname, iterate):

    labellist = ['V', 'S', 'F', 'A']

    # Setup main figure
    setup_plot(usetex=True)
    fig = plt.figure(figsize=(5,5))
    grid = AxesGrid(fig, 111, nrows_ncols=(1, 1), axes_pad=0.0, share_all=True,\
                    label_mode="L", cbar_location="right", cbar_mode="single", cbar_size='6%')

    if INTERACTIVE == True:
        contour_offset = input("Enter value of minimum isophote [default: 0.20]: ")
        if contour_offset == '': contour_offset = 0.20
        else:                    contour_offset = float(contour_offset)
    else: 
        contour_offset = 0.20

    # Prepare main plot
    if iterate == 0: val = gandalf_Vel[:,line_idx]
    if iterate == 1: val = gandalf_Sigma[:,line_idx]
    if iterate == 2: val = np.log10( gandalf_Flux[:,line_idx] )
    if iterate == 3: val = gandalf_Ampl[:,line_idx]

    if len( np.where( np.isnan(val) == True )[0] ) == len(val):
        return(None)

    if INTERACTIVE == True:
        # Interactive Mode: Prompt for values of vmin/vmax, show plot and iterate until you are satisfied
        inp = input(" Enter vmin,vmax for "+labellist[iterate]+\
                    "! Good guess: "+'[{:.2f},{:.2f}]'.format(np.nanmin(val),np.nanmax(val))+\
                    "; Previously chosen: ["+str(vminmax[iterate,0])+","+str(vminmax[iterate,1])+\
                    "]; New values: ")
        if inp == '':
            # Hit ENTER to keep previously selected values
            vmin = vminmax[iterate,0]
            vmax = vminmax[iterate,1]
        else:
            # Use input values for vmin,vmax and save them for later
            vmin = float(inp.split(',')[0])
            vmax = float(inp.split(',')[1])
            vminmax[iterate,0] = vmin
            vminmax[iterate,1] = vmax
    else:
        if SAVE_AFTER_INTERACTIVE == False:
            # Determine vmin/vmax automatically, if called from within the pipeline
            vmin = np.nanmin(val)
            vmax = np.nanmax(val)
        elif SAVE_AFTER_INTERACTIVE == True:
            # Use previously selected values, redo plot and save!
            vmin = vminmax[iterate,0]
            vmax = vminmax[iterate,1]

    # Create image in pixels
    xmin = np.nanmin(X)-6;  xmax = np.nanmax(X)+6
    ymin = np.nanmin(Y)-6;  ymax = np.nanmax(Y)+6
    npixels_x = int( np.round( (xmax - xmin)/pixelsize ) + 1 )
    npixels_y = int( np.round( (ymax - ymin)/pixelsize ) + 1 )
    i = np.array( np.round( (X - xmin)/pixelsize ), dtype=np.int )
    j = np.array( np.round( (Y - ymin)/pixelsize ), dtype=np.int )
    image = np.full( (npixels_x, npixels_y), np.nan )
    image[i,j] = val

    # Plot map and colorbar
    image = grid[0].imshow(np.rot90(image), cmap='sauron', interpolation=None, vmin=vmin, vmax=vmax, \
        extent=[xmin-pixelsize/2, xmax+pixelsize/2, ymin-pixelsize/2, ymax+pixelsize/2])
    grid.cbar_axes[0].colorbar(image)

    # Plot contours
    XY_Triangulation = Triangulation(X-pixelsize/2, Y-pixelsize/2)                      # Create a mesh from a Delaunay triangulation
    XY_Triangulation.set_mask( TriAnalyzer(XY_Triangulation).get_flat_tri_mask(0.01) )  # Remove bad triangles at the border of the field-of-view
    levels = np.arange( np.min(np.log10( FLUX )) + contour_offset, np.max(np.log10( FLUX )), 0.2 )
    grid[0].tricontour(XY_Triangulation, np.log10(FLUX), levels=levels, linewidths=1, colors='k')

    # Label vmin and vmax
    if iterate == 0  or  iterate == 1:
        grid[0].text(0.985,0.008 ,r'\textbf{{{:.0f}}}'.format(vmin).replace("-", r"\textendash\,")+r'\textbf{ / }'+r'\textbf{{{:.0f}}}'.format(vmax), \
                horizontalalignment='right', verticalalignment='bottom', transform = grid[0].transAxes, fontsize=16)
    if iterate == 2  or  iterate == 3:
        grid[0].text(0.985,0.008 ,r'\textbf{{{:.2f}}}'.format(vmin).replace("-", r"\textendash\,")+r'\textbf{ / }'+r'\textbf{{{:.2f}}}'.format(vmax), \
                horizontalalignment='right', verticalalignment='bottom', transform = grid[0].transAxes, fontsize=16)

    # Remove ticks and labels from colorbar
    for cax in grid.cbar_axes:
        cax.toggle_label(False)
        cax.yaxis.set_ticks([])

    # Set labels
    grid[0].text(0.985, 0.975, r'\textbf{{{}}}'.format(rootname), horizontalalignment='right', verticalalignment='top', transform = grid[0].transAxes, fontsize=16)    
    if iterate == 0: 
        grid[0].text(0.02, 0.98, r'$V \mathrm{[km/s]}$',      horizontalalignment='left', verticalalignment='top', transform = grid[0].transAxes, fontsize=16)
    elif iterate == 1:
        grid[0].text(0.02, 0.98, r'$\sigma \mathrm{[km/s]}$', horizontalalignment='left', verticalalignment='top', transform = grid[0].transAxes, fontsize=16)
    elif iterate == 2:
        grid[0].text(0.02, 0.98, r'\textbf{Flux}',            horizontalalignment='left', verticalalignment='top', transform = grid[0].transAxes, fontsize=16)
    elif iterate == 3:
        grid[0].text(0.02, 0.98, r'\textbf{Ampl}',            horizontalalignment='left', verticalalignment='top', transform = grid[0].transAxes, fontsize=16)

    if lineIdentifier[0] == 'Ha':
        grid[0].text( 0.02, 0.008, r'$\mathbf{H\alpha}$', \
                horizontalalignment='left',verticalalignment='bottom', transform = grid[0].transAxes, fontsize=16)
    elif lineIdentifier[0] == 'Hb':
        grid[0].text( 0.02, 0.008, r'$\mathbf{H\beta}$', \
                horizontalalignment='left',verticalalignment='bottom', transform = grid[0].transAxes, fontsize=16)
    else:
        grid[0].text( 0.02, 0.008, r'\textbf{'+lineIdentifier[0].replace('[','').replace(']','')+'}', \
                horizontalalignment='left',verticalalignment='bottom', transform = grid[0].transAxes, fontsize=16)

    # Set xlabel and ylabel
    grid[0].set_xlabel(r'$\Delta \alpha$ \textbf{[arcsec]}')
    grid[0].set_ylabel(r'$\Delta \delta$ \textbf{[arcsec]}')

    # Fix minus sign in ticklabels
    grid[0].xaxis.set_major_formatter(FuncFormatter(TicklabelFormatter))
    grid[0].yaxis.set_major_formatter(FuncFormatter(TicklabelFormatter))

    # Invert x-axis
    grid[0].invert_xaxis()

    # Set tick frequency and parameters
    grid[0].xaxis.set_major_locator(MultipleLocator(10));  grid[0].yaxis.set_major_locator(MultipleLocator(10))  # Major tick every 10 units
    grid[0].xaxis.set_minor_locator(MultipleLocator(1));   grid[0].yaxis.set_minor_locator(MultipleLocator(1))   # Minor tick every 1 units
    grid[0].tick_params(direction="in", which='both', bottom=True, top=True, left=True, right=True)              # Ticks inside of plot

    if INTERACTIVE == True:
        # Display preview of plot in INTERACTIVE-mode and decide if another iteration is necessary
        plt.show()
        inp = input(" Save plot [y/n]? ")
        print("")
        if inp == 'y' or inp == 'Y' or inp == 'yes' or inp == 'YES':
            # To save plot with previously selected values: 
            #   Call function again with previously chosen values for vmin and vmax, then save figure to file without prompting again
            plt.close(); fig.clf()
            plot_line(LEVEL, FROM_PIPELINE, gandalf_Vel, gandalf_Sigma, gandalf_Flux, gandalf_Ampl, False, True,\
                      runname, AoNThreshold, line_idx, lineIdentifier, vminmax, contour_offset_saved, X, Y, FLUX, pixelsize, outdir, rootname, iterate)

        elif inp == 'n' or inp == 'N' or inp == 'no' or inp == 'NO':
            # To iterate and prompt again:
            #   Call function again with new values for vmin and vmax (offer previously chosen values as default), then prompt again
            plt.close(); fig.clf()
            plot_line(LEVEL, FROM_PIPELINE, gandalf_Vel, gandalf_Sigma, gandalf_Flux, gandalf_Ampl, True, False,\
                      runname, AoNThreshold, line_idx, lineIdentifier, vminmax, contour_offset_saved, X, Y, FLUX, pixelsize, outdir, rootname, iterate)
        else:
            print("You should have hit 'y' or 'n'. I guess you want to try another time?!")
            # To iterate and prompt again:
            #   Call function again with new values for vmin and vmax (offer previously chosen values as default), then prompt again
            plt.close(); fig.clf()
            plot_line(LEVEL, FROM_PIPELINE, gandalf_Vel, gandalf_Sigma, gandalf_Flux, gandalf_Ampl, True, False,\
                      runname, AoNThreshold, line_idx, lineIdentifier, vminmax, contour_offset_saved, X, Y, FLUX, pixelsize, outdir, rootname, iterate)
    else:
        # Save plot in non-interactive mode or when called from within the pipeline
        plt.savefig(outdir+rootname+'_gandalf-'+lineIdentifier[0]+lineIdentifier[1]+'_'+labellist[iterate]+'_'+LEVEL+'.pdf', bbox_inches='tight', pad_inches=0.3)
           

def plot_maps(outdir, LEVEL, FROM_PIPELINE, INTERACTIVE=False, vminmax=np.zeros((4,2)), SAVE_AFTER_INTERACTIVE=False, AoNThreshold=4, line_idx=None, plottype=None):

    runname  = outdir
    rootname = outdir.split('/')[-2].split('_')[0]

    # Read bintable
    table_hdu = fits.open(outdir+rootname+'_table.fits')
    X           = np.array( table_hdu[1].data.X ) * -1
    Y           = np.array( table_hdu[1].data.Y )
    FLUX        = np.array( table_hdu[1].data.FLUX )
    binNum_long = np.array( table_hdu[1].data.BIN_ID )
    ubins       = np.unique( np.abs(binNum_long) )
    pixelsize   = table_hdu[0].header['PIXSIZE']

    # Check spatial coordinates
    if len( np.where( np.logical_or( X == 0.0, np.isnan(X) == True ) )[0] ) == len(X):
        print('All X-coordinates are 0.0 or np.nan. Plotting maps will not work without reasonable spatial information!')
    if len( np.where( np.logical_or( Y == 0.0, np.isnan(Y) == True ) )[0] ) == len(Y):
        print('All Y-coordinates are 0.0 or np.nan. Plotting maps will not work without reasonable spatial information!\n')

    # Read Gandalf results
    if LEVEL == 'SPAXEL':
        gandalf_emisetup = fits.open(outdir+rootname+'_gandalf_SPAXEL.fits')[1].data
        gandalf_raw      = fits.open(outdir+rootname+'_gandalf_SPAXEL.fits')[2].data
    elif LEVEL == 'BIN':
        gandalf_emisetup = fits.open(outdir+rootname+'_gandalf_BIN.fits')[1].data
        gandalf_raw      = fits.open(outdir+rootname+'_gandalf_BIN.fits')[2].data
    gandalf_Flux  = np.array( gandalf_raw.FLUX  )
    gandalf_Ampl  = np.array( gandalf_raw.AMPL  )
    gandalf_Vel   = np.array( gandalf_raw.V     )
    gandalf_Sigma = np.array( gandalf_raw.SIGMA )
    gandalf_AoN   = np.array( gandalf_raw.AON   )

    # Convert results to long version
    if LEVEL == 'BIN':
        gandalf_Flux_long = np.zeros( (len(binNum_long), gandalf_Flux.shape[1]) );  gandalf_Flux_long[:,:] = np.nan
        gandalf_Ampl_long = np.zeros( (len(binNum_long), gandalf_Ampl.shape[1]) );  gandalf_Ampl_long[:,:] = np.nan
        gandalf_Vel_long  = np.zeros( (len(binNum_long), gandalf_Vel.shape[1])  );  gandalf_Vel_long[:,:]  = np.nan
        gandalf_Sigma_long= np.zeros( (len(binNum_long), gandalf_Sigma.shape[1]));  gandalf_Sigma_long[:,:]= np.nan
        gandalf_AoN_long  = np.zeros( (len(binNum_long), gandalf_AoN.shape[1])  );  gandalf_AoN_long[:,:]  = np.nan
        for i in range( len(ubins) ):
            idx = np.where( ubins[i] == np.abs(binNum_long) )[0]
            gandalf_Flux_long[idx,:] = gandalf_Flux[i,:]
            gandalf_Ampl_long[idx,:] = gandalf_Ampl[i,:]
            gandalf_Vel_long[idx,:]  = gandalf_Vel[i,:]
            gandalf_Sigma_long[idx,:]= gandalf_Sigma[i,:]
            gandalf_AoN_long[idx,:]  = gandalf_AoN[i,:]
        gandalf_Flux    = gandalf_Flux_long
        gandalf_Ampl    = gandalf_Ampl_long
        gandalf_Vel     = gandalf_Vel_long
        gandalf_Sigma   = gandalf_Sigma_long
        gandalf_AoN     = gandalf_AoN_long

    gandalf_Flux  = np.array( gandalf_Flux  )
    gandalf_Ampl  = np.array( gandalf_Ampl  )
    gandalf_Vel   = np.array( gandalf_Vel   )
    gandalf_Sigma = np.array( gandalf_Sigma )
    gandalf_AoN   = np.array( gandalf_AoN   )
    X             = np.array( X             )
    Y             = np.array( Y             )

    # Get list of emission lines
    linelist = []
    for i in range( len(gandalf_emisetup.name) ):
        linelist.append( [gandalf_emisetup.name[i].decode('utf-8'), str(gandalf_emisetup._lambda[i])] )

    # Apply AoN threshold to GANDALF
    for i in range(0, gandalf_AoN.shape[1]):
        idx_AoNThreshold = np.where( gandalf_AoN[:,i] < AoNThreshold )[0]
        gandalf_Flux[idx_AoNThreshold,i]  = np.nan
        gandalf_Ampl[idx_AoNThreshold,i]  = np.nan
        gandalf_Vel[idx_AoNThreshold,i]   = np.nan
        gandalf_Sigma[idx_AoNThreshold,i] = np.nan
        gandalf_AoN[idx_AoNThreshold,i]   = np.nan

    gandalf_Flux[ np.where(gandalf_Flux ==-1)[0] ] = np.nan
    gandalf_Ampl[ np.where(gandalf_Ampl ==-1)[0] ] = np.nan
    gandalf_Vel[  np.where(gandalf_Vel  ==-1)[0] ] = np.nan
    gandalf_Sigma[np.where(gandalf_Sigma==-1)[0] ] = np.nan

    gandalf_Vel   = gandalf_Vel - np.nanmedian( gandalf_Vel )

    # Create/Set output directory
    if os.path.isdir(outdir+'maps/') == False:
        os.mkdir(outdir+'maps/')
    outdir = outdir+'maps/'

    if FROM_PIPELINE == False:
        lineIdentifier = linelist[int(line_idx)]
        if plottype == 'V': iterate = 0
        elif plottype == 'S': iterate = 1
        elif plottype == 'F': iterate = 2
        elif plottype == 'A': iterate = 3
        else: print("No plottype set. Exit!"); exit(1)

        plot_line(LEVEL, FROM_PIPELINE, gandalf_Vel, gandalf_Sigma, gandalf_Flux, gandalf_Ampl, INTERACTIVE, SAVE_AFTER_INTERACTIVE,\
                  runname, AoNThreshold, int(line_idx), lineIdentifier, vminmax, 0.20, X, Y, FLUX, pixelsize, outdir, rootname, iterate)

    elif FROM_PIPELINE == True:
        # Iterate over all lines
        for line_idx, lineIdentifier in enumerate( linelist ):
            # Iterate over V, Sigma, A, F
            for iterate in range(0,4):
                plot_line(LEVEL, FROM_PIPELINE, gandalf_Vel, gandalf_Sigma, gandalf_Flux, gandalf_Ampl, INTERACTIVE, SAVE_AFTER_INTERACTIVE,\
                          runname, AoNThreshold, int(line_idx), lineIdentifier, vminmax, 0.20, X, Y, FLUX, pixelsize, outdir, rootname, iterate)


# ==============================================================================
# If plot routine is run independently of pipeline
def main(args=None):
    # Capturing the command line arguments
    parser = optparse.OptionParser(usage="./utilities/util_plot_gandalf.py --runname=FCC167_Full-Opt --aon=4 --level=SPAXEL --line=12 --type=V")
    parser.add_option("-r", "--runname", dest="runname",       type="string", help="Path of output directory."                                 )
    parser.add_option("-l", "--level",   dest="LEVEL",         type="string", help="Plot data either on BIN or SPAXEL level"                   )
    parser.add_option("-e", "--line",    dest="line",          type="string", help="LINE_ID, as specified in  '_gandalf_*.fits' extension 1"   )
    parser.add_option("-t", "--type",    dest="plottype",      type="string", help="Extracted information to be plotted: V, Sigma, A or F"     )
    parser.add_option("-a", "--aon",     dest="aon_threshold", type="int",    help="Minimum AoN of data to be plotted"                         )
    (options, args) = parser.parse_args()

    if options.runname[-1] != '/':
        options.runname = options.runname+'/'

    plot_maps(options.runname, options.LEVEL, False, INTERACTIVE=True, AoNThreshold=options.aon_threshold, line_idx=options.line, plottype=options.plottype)


if __name__ == '__main__':
    # Cal the main function
    main()

