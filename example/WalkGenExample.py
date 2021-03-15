import matplotlib.pyplot as plt
import numpy
import logging, asyncio
from WalkGenerator import WalkPatternGenerator

ENABLE_PLOTTING = True


def plot2d(x, y, title="", legend="", overwrite=True):
    if not overwrite:
        fig = plt.figure()
        subplot1 = fig.add_subplot( 111 )
        subplot1.title( title )
        subplot1.plot( x, y, label=legend )
    else:
        plt.title( title )
        plt.plot( x, y, label=legend )


def plot3d(x, y, z, title="", legend="", overwrite=False):
    if not overwrite:
        fig = plt.figure()
        subplot1 = fig.add_subplot( 111, projection='3d' )
        subplot1.title( title )
        subplot1.plot( x, y, z, label=legend )
    else:
        plt.title( title )
        plt.plot( x, y, label=legend )


async def walk_pattern_test(event_loop):
    number_of_samples = 100
    if ENABLE_PLOTTING:
        x_ref_pos = numpy.zeros( number_of_samples )
        y_ref_pos = numpy.zeros( number_of_samples )
        z_ref_pos = numpy.zeros( number_of_samples )
        x_outlier_pos = numpy.zeros( number_of_samples )
        y_outlier_pos = numpy.zeros( number_of_samples )
        z_outlier_pos = numpy.zeros( number_of_samples )
        input_sample = numpy.zeros( number_of_samples )

    walker = WalkPatternGenerator( eventloop=event_loop, config_file="personnel.yaml", personnel_id=1 )
    await walker.connect()

    for i in range( 1, number_of_samples ):
        await walker.run_once( tdelta=0.7, binding_key="telemetry" )
        states = walker.get_states()

        # update states
        if ENABLE_PLOTTING:
            x_ref_pos[i] = states["x_ref_pos"]
            y_ref_pos[i] = states["y_ref_pos"]
            z_ref_pos[i] = states["z_ref_pos"]
            x_outlier_pos[i] = states["x_outlier_pos"]
            y_outlier_pos[i] = states["y_outlier_pos"]
            z_outlier_pos[i] = states["z_outlier_pos"]
            input_sample[i] = i

    # Plot
    if ENABLE_PLOTTING:
        fig1 = plt.figure()
        fig1plot1 = fig1.add_subplot( 311 )
        fig1plot1.title.set_text( "Random Walk x-axis" )
        fig1plot1.set_xlabel( "steps" )
        fig1plot1.set_ylabel( "position" )
        fig1plot1.plot( input_sample, x_outlier_pos,
                        label="outlier", color="r", linestyle="-", marker="." )
        fig1plot1.plot( input_sample, x_ref_pos, label="actual",
                        color="g", linestyle="--", marker="." )

        fig1plot2 = fig1.add_subplot( 312 )
        fig1plot2.title.set_text( "Random Walk y-axis" )
        fig1plot2.set_xlabel( "steps" )
        fig1plot2.set_ylabel( "position" )
        fig1plot2.plot( input_sample, y_outlier_pos,
                        label="outlier", color="r", linestyle="-", marker="." )
        fig1plot2.plot( input_sample, y_ref_pos, label="actual",
                        color="g", linestyle="--", marker="." )

        fig1plot3 = fig1.add_subplot( 313 )
        fig1plot3.title.set_text( "Random Walk z-axis" )
        fig1plot3.set_xlabel( "steps" )
        fig1plot3.set_ylabel( "position" )
        fig1plot3.plot( input_sample, z_outlier_pos,
                        label="outlier", color="r", linestyle="-", marker="." )
        fig1plot3.plot( input_sample, z_ref_pos, label="actual",
                        color="g", linestyle="--", marker="." )

        fig2 = plt.figure()
        fig2plot1 = fig2.add_subplot( 111, projection='3d' )
        fig2plot1.title.set_text( "Random Walk 3D" )
        fig2plot1.set_xlabel( "x position" )
        fig2plot1.set_ylabel( "y position" )
        fig2plot1.set_zlabel( "z position" )
        fig2plot1.plot( x_outlier_pos, y_outlier_pos,
                        z_outlier_pos, label="outlier", color="r", linestyle="--" )
        fig2plot1.plot( x_ref_pos, y_ref_pos, z_ref_pos,
                        label="actual", color="g", linestyle="--" )

        fig3 = plt.figure()
        fig3plot1 = fig3.add_subplot( 111 )
        fig3plot1.title.set_text( "Random Walk 2D" )
        fig3plot1.set_xlabel( "x position" )
        fig3plot1.set_ylabel( "y position" )
        fig3plot1.plot( x_outlier_pos, y_outlier_pos,
                        label="outlier", color="r", linestyle="--" )
        fig3plot1.plot( x_ref_pos, y_ref_pos,
                        label="actual", color="g", linestyle="--" )

        plt.legend()
        plt.show()


async def walk_forever(eventloop):
    walker = WalkPatternGenerator( eventloop=eventloop, config_file="personnel.yaml", personnel_id=1 )
    await walker.connect()
    while True:
        await walker.run_once( tdelta=0.7, binding_key="telemetry" )


if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete( walk_forever( event_loop ) )
