#!/usr/bin/env python

from   astropy.io import fits
import numpy      as np
import os
import optparse
import warnings
warnings.filterwarnings('ignore')
from matplotlib.tri import Triangulation, TriAnalyzer

import matplotlib.pyplot       as     plt
from   mpl_toolkits.axes_grid1 import AxesGrid
from   matplotlib.ticker       import MultipleLocator, FuncFormatter

from plotbin.sauron_colormap import register_sauron_colormap
register_sauron_colormap()


"""
PURPOSE:
  Plot maps of the stellar kinematics. This routine can be applied to kinematics
  generated by both the stellarKinematics (KIN) and starFormationHistories (SFH)
  module. 
  
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


def plotMaps(flag, outdir, INTERACTIVE=False, vminmax=np.zeros((4,2)), contour_offset_saved=0.20, SAVE_AFTER_INTERACTIVE=False):

    labellist = ['V', 'SIGMA', 'H3', 'H4']

    runname  = outdir 
    rootname = outdir.rstrip('/').split('/')[-1]

    # Read bintable
    table_hdu = fits.open(os.path.join(outdir,rootname)+'_table.fits')
    idx_inside  = np.where( table_hdu[1].data.BIN_ID >= 0        )[0]
    X           = np.array( table_hdu[1].data.X[idx_inside]      ) * -1
    Y           = np.array( table_hdu[1].data.Y[idx_inside]      )
    FLUX        = np.array( table_hdu[1].data.FLUX[idx_inside]   )
    binNum_long = np.array( table_hdu[1].data.BIN_ID[idx_inside] )
    ubins       = np.unique( np.abs( np.array( table_hdu[1].data.BIN_ID ) ) )
    pixelsize   = table_hdu[0].header['PIXSIZE']

    # Check spatial coordinates
    if len( np.where( np.logical_or( X == 0.0, np.isnan(X) == True ) )[0] ) == len(X):
        print('All X-coordinates are 0.0 or np.nan. Plotting maps will not work without reasonable spatial information!')
    if len( np.where( np.logical_or( Y == 0.0, np.isnan(Y) == True ) )[0] ) == len(Y):
        print('All Y-coordinates are 0.0 or np.nan. Plotting maps will not work without reasonable spatial information!\n')

    # Read Results
    if flag == 'KIN':
        hdu = fits.open(os.path.join(outdir,rootname)+'_kin.fits')
    elif flag == 'SFH':
        hdu = fits.open(os.path.join(outdir,rootname)+'_sfh.fits')
    result      = np.zeros((len(ubins),4))
    result[:,0] = np.array( hdu[1].data.V     )
    result[:,1] = np.array( hdu[1].data.SIGMA )
    if hasattr(ppxf, 'H3'): result[:,2] = np.array(hdu[1].data.H3)
    if hasattr(ppxf, 'H4'): result[:,3] = np.array(hdu[1].data.H4)

    # Convert results to long version
    result_long  = np.zeros( (len(binNum_long), result.shape[1]) ); result_long[:,:] = np.nan
    for i in range( len(ubins) ):
        idx = np.where( ubins[i] == np.abs(binNum_long) )[0]
        result_long[idx,:]  = result[i,:]
    result = result_long
    result[:,0] = result[:,0] - np.nanmedian( result[:,0] )

    # Create/Set output directory
    if os.path.isdir(os.path.join(outdir,'maps/')) == False:
        os.mkdir(os.path.join(outdir,'maps/'))
    outdir = os.path.join(outdir,'maps/')

    # Setup main figure
    setup_plot(usetex=True)
    fig = plt.figure(figsize=(10,10))
    grid = AxesGrid(fig, 111, nrows_ncols=(2, 2), axes_pad=0.0, share_all=True,\
                    label_mode="L", cbar_location="right", cbar_mode="single", cbar_size='4%')

    if INTERACTIVE == True:
        contour_offset = input("Enter value of minimum isophote [Previously: {:.2f}]: ".format(contour_offset_saved))
        if contour_offset == '': contour_offset = contour_offset_saved
        else:                    contour_offset = float(contour_offset)
    else: 
        contour_offset = contour_offset_saved

    for iterate in range(0,4):
        # Prepare main plot
        val = result[:,iterate]

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
        image = grid[iterate].imshow(np.rot90(image), cmap='sauron', interpolation=None, vmin=vmin, vmax=vmax, \
            extent=[xmin-pixelsize/2, xmax+pixelsize/2, ymin-pixelsize/2, ymax+pixelsize/2] )
        grid.cbar_axes[iterate].colorbar(image)

        # Plot contours
        XY_Triangulation = Triangulation(X-pixelsize/2, Y-pixelsize/2)                      # Create a mesh from a Delaunay triangulation
        XY_Triangulation.set_mask( TriAnalyzer(XY_Triangulation).get_flat_tri_mask(0.01) )  # Remove bad triangles at the border of the field-of-view
        levels = np.arange( np.min(np.log10( FLUX )) + contour_offset, np.max(np.log10( FLUX )), 0.2 )
        grid[iterate].tricontour(XY_Triangulation, np.log10(FLUX), levels=levels, linewidths=1, colors='k')

        # Label vmin and vmax
        if iterate in [0,1]: 
            grid[iterate].text(0.985,0.008 ,r'\textbf{{{:.0f}}}'.format(vmin).replace("-", r"\textendash\,")+r'\textbf{ / }'+r'\textbf{{{:.0f}}}'.format(vmax), \
                    horizontalalignment='right', verticalalignment='bottom', transform = grid[iterate].transAxes, fontsize=16)
        elif iterate in [2,3]:
            grid[iterate].text(0.985,0.008 ,r'\textbf{{{:.2f}}}'.format(vmin).replace("-", r"\textendash\,")+r'\textbf{ / }'+r'\textbf{{{:.2f}}}'.format(vmax), \
                    horizontalalignment='right', verticalalignment='bottom', transform = grid[iterate].transAxes, fontsize=16)

    # Remove ticks and labels from colorbar
    for cax in grid.cbar_axes:
        cax.toggle_label(False)
        cax.yaxis.set_ticks([])

    # Set V, SIGMA, H3, H4 labels
    grid[0].text(0.02,  0.975, r'$V_{\mathrm{stellar}} \mathrm{[km/s]}$',      horizontalalignment='left',  verticalalignment='top', transform = grid[0].transAxes, fontsize=16)
    grid[0].text(0.985, 0.975, r'\textbf{{{}}}'.format(rootname),              horizontalalignment='right', verticalalignment='top', transform = grid[0].transAxes, fontsize=16)    
    grid[1].text(0.02,  0.98 , r'$\sigma_{\mathrm{stellar}} \mathrm{[km/s]}$', horizontalalignment='left',  verticalalignment='top', transform = grid[1].transAxes, fontsize=16)
    grid[2].text(0.02,  0.98 , r'\textbf{h3}',                                 horizontalalignment='left',  verticalalignment='top', transform = grid[2].transAxes, fontsize=16)
    grid[3].text(0.02,  0.98 , r'\textbf{h4}',                                 horizontalalignment='left',  verticalalignment='top', transform = grid[3].transAxes, fontsize=16)

    # Set xlabel and ylabel
    grid[0].set_ylabel(r'$\Delta \delta$ \textbf{[arcsec]}')
    grid[2].set_ylabel(r'$\Delta \delta$ \textbf{[arcsec]}')
    grid[2].set_xlabel(r'$\Delta \alpha$ \textbf{[arcsec]}')
    grid[3].set_xlabel(r'$\Delta \alpha$ \textbf{[arcsec]}')

    # Fix minus sign in ticklabels
    grid[0].xaxis.set_major_formatter(FuncFormatter(TicklabelFormatter))
    grid[0].yaxis.set_major_formatter(FuncFormatter(TicklabelFormatter))

    # Invert x-axis
    grid[0].invert_xaxis()
    grid[1].invert_xaxis()
    grid[2].invert_xaxis()
    grid[3].invert_xaxis()

    # Set tick frequency and parameters
    for iterate in range(0,4):
        grid[iterate].xaxis.set_major_locator(MultipleLocator(10));  grid[iterate].yaxis.set_major_locator(MultipleLocator(10))  # Major tick every 10 units
        grid[iterate].xaxis.set_minor_locator(MultipleLocator(1));   grid[iterate].yaxis.set_minor_locator(MultipleLocator(1))   # Minor tick every 1 units
        grid[iterate].tick_params(direction="in", which='both', bottom=True, top=True, left=True, right=True)                    # Ticks inside of plot

    if INTERACTIVE == True:
        # Display preview of plot in INTERACTIVE-mode and decide if another iteration is necessary
        plt.show()
        inp = input(" Save plot [y/n]? ")
        print("")
        if inp == 'y' or inp == 'Y' or inp == 'yes' or inp == 'YES':
            # To save plot with previously selected values: 
            #   Call function again with previously chosen values for vmin and vmax, then save figure to file without prompting again
            plotMaps(flag, runname, INTERACTIVE=False, vminmax=vminmax, contour_offset_saved=contour_offset, SAVE_AFTER_INTERACTIVE=True)
        elif inp == 'n' or inp == 'N' or inp == 'no' or inp == 'NO':
            # To iterate and prompt again:
            #   Call function again with new values for vmin and vmax (offer previously chosen values as default), then prompt again
            plotMaps(flag, runname, INTERACTIVE=True, vminmax=vminmax, contour_offset_saved=contour_offset, SAVE_AFTER_INTERACTIVE=False)
        else:
            print("You should have hit 'y' or 'n'. I guess you want to try another time?!")
            # To iterate and prompt again:
            #   Call function again with new values for vmin and vmax (offer previously chosen values as default), then prompt again
            plotMaps(flag, runname, INTERACTIVE=True, vminmax=vminmax, contour_offset_saved=contour_offset, SAVE_AFTER_INTERACTIVE=False)

    else:
        # Save plot in non-interactive mode or when called from within the pipeline
        if flag == 'KIN':
            plt.savefig(os.path.join(outdir,rootname)+'_kin.pdf', bbox_inches='tight', pad_inches=0.3)
        elif flag == 'SFH':
            plt.savefig(os.path.join(outdir,rootname)+'_sfh-kin.pdf', bbox_inches='tight', pad_inches=0.3)

    fig.clf()
    plt.close()

# ==============================================================================
# If plot routine is run independently of pipeline
def main(args=None):
    # Capturing the command line arguments
    parser = optparse.OptionParser(usage="%prog -f flag")
    parser.add_option("-f", "--flag",    dest="flag",    type="string", help="Select whether you want to plot stellar kinematics from the stellarKinematics (KIN) or starFormatioHistories (SFH) module.")
    parser.add_option("-r", "--runname", dest="runname", type="string", help="Path to output directory.")
    (options, args) = parser.parse_args()

    if options.runname[-1] != '/':
        options.runname = options.runname+'/'

    plotMaps(options.flag, options.runname, INTERACTIVE=True)


if __name__ == '__main__':
    # Call the main function
    main()
