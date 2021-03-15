import json
import os
import sys
import traceback
import yaml
import logging, asyncio
from OutlierGenerator import OutlierGenerator
from AMQPubSub import AMQ_Pub_Sub


class PositioningTag:
    def __init__(self, eventloop, config_file, personnel_id):
        try:
            if os.path.exists( config_file ):
                with open( config_file, 'r' ) as yaml_file:
                    yaml_as_dict = yaml.load( yaml_file, Loader=yaml.FullLoader )

                    # extract data from yaml config file
                    personnel_info = yaml_as_dict["walk_generator"]["personnel"]
                    walk_property_info = yaml_as_dict["walk_generator"]["property"]

                    # The personnel id of instance must be specified in yaml config file. If not raise Assertion error
                    person_info = None
                    for personnel in personnel_info:
                        if personnel["id"] == personnel_id:
                            person_info = personnel
                            break;
                    assert (person_info is not None), f"personnel_id: {personnel_id} does not exists in configuration file"

                    self.walk_dimension = walk_property_info["walk"]["walk_dimension"]
                    self.outlier_model_x = OutlierGenerator( mean=walk_property_info["positioning"]["outliers"]["x"]["mean"],
                                                             standard_deviation=walk_property_info["positioning"]["outliers"]["x"]["standard_deviation"],
                                                             number_of_outliers=walk_property_info["positioning"]["outliers"]["x"]["number_of_outlier"],
                                                             sample_size=walk_property_info["positioning"]["outliers"]["x"]["sample_size"] )

                    self.outlier_model_y = OutlierGenerator( mean=walk_property_info["positioning"]["outliers"]["y"]["mean"],
                                                             standard_deviation=walk_property_info["positioning"]["outliers"]["y"]["standard_deviation"],
                                                             number_of_outliers=walk_property_info["positioning"]["outliers"]["y"]["number_of_outlier"],
                                                             sample_size=walk_property_info["positioning"]["outliers"]["y"]["sample_size"] )

                    self.outlier_model_z = OutlierGenerator( mean=walk_property_info["positioning"]["outliers"]["z"]["mean"],
                                                             standard_deviation=walk_property_info["positioning"]["outliers"]["z"]["standard_deviation"],
                                                             number_of_outliers=walk_property_info["positioning"]["outliers"]["z"]["number_of_outlier"],
                                                             sample_size=walk_property_info["positioning"]["outliers"]["z"]["sample_size"] )

                    self.eventloop = eventloop
                    self.publisher = AMQ_Pub_Sub( eventloop=self.eventloop, config_file=config_file, pub_sub_name=person_info["pub_sub_name"], mode="pub" )

                    self.x_outlier_pos = 0
                    self.y_outlier_pos = 0
                    self.z_outlier_pos = 0

        except FileNotFoundError as e:
            logging.critical( e )
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.critical( repr( traceback.format_exception( exc_type, exc_value, exc_traceback ) ) )
            sys.exit()
        except OSError as e:
            logging.critical( e )
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.critical( repr( traceback.format_exception( exc_type, exc_value, exc_traceback ) ) )
            sys.exit()
        except AssertionError as e:
            logging.critical( e )
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.critical( repr( traceback.format_exception( exc_type, exc_value, exc_traceback ) ) )
            sys.exit()
        except yaml.YAMLError as e:
            logging.critical( e )
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.critical( repr( traceback.format_exception( exc_type, exc_value, exc_traceback ) ) )
            sys.exit()
        except:
            logging.critical( "unhandled exception" )
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.critical( repr( traceback.format_exception( exc_type, exc_value, exc_traceback ) ) )
            sys.exit()

    async def _publish(self, binding_key, msg):
        await self.publisher.publish( binding_key=binding_key, message_content=msg )

    def _update3d(self, reference_position):
        try:
            x_ref_pos = reference_position["x_ref_pos"]
            y_ref_pos = reference_position["y_ref_pos"]
            z_ref_pos = reference_position["z_ref_pos"]

            # check for outlier model
            if self.walk_dimension == 1:
                if self.outlier_model_x is not None:
                    self.x_outlier_pos = x_ref_pos + self.outlier_model_x.generate()
                self.y_outlier_pos = y_ref_pos
                self.z_outlier_pos = z_ref_pos

            elif self.walk_dimension == 2:
                if self.outlier_model_x is not None:
                    self.x_outlier_pos = x_ref_pos + self.outlier_model_x.generate()
                if self.outlier_model_y is not None:
                    self.y_outlier_pos = y_ref_pos + self.outlier_model_y.generate()
                self.z_outlier_pos = z_ref_pos
            else:
                if self.outlier_model_x is not None:
                    self.x_outlier_pos = x_ref_pos + self.outlier_model_x.generate()
                if self.outlier_model_y is not None:
                    self.y_outlier_pos = y_ref_pos + self.outlier_model_y.generate()
                if self.outlier_model_z is not None:
                    self.z_outlier_pos = z_ref_pos + self.outlier_model_z.generate()

            return {"x_ref_pos": x_ref_pos, "y_ref_pos": y_ref_pos, "z_ref_pos": z_ref_pos,
                    "x_outlier_pos": self.x_outlier_pos, "y_outlier_pos": self.y_outlier_pos, "z_outlier_pos": self.z_outlier_pos}
        except AssertionError as e:
            logging.critical( e )
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.critical( repr( traceback.format_exception( exc_type, exc_value, exc_traceback ) ) )
            sys.exit()
        except:
            logging.critical( "unhandled exception" )
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.critical( repr( traceback.format_exception( exc_type, exc_value, exc_traceback ) ) )
            sys.exit()

    async def connect(self):
        await self.publisher.connect()

    async def run_once(self, reference_position, tdelta=-1, binding_key=None):
        result = dict()
        result.update( self._update3d( reference_position=reference_position ) )

        # Publish
        if binding_key is not None:
            await self._publish( binding_key=binding_key, msg=json.dumps( result ).encode() )

        # sleep until its time for next sample
        if tdelta >= 0:
            await asyncio.sleep( delay=tdelta )
        else:
            await asyncio.sleep( delay=0 )

    def update_once(self, reference_position):
        result = dict()
        result.update( self._update3d( reference_position=reference_position ) )
        return result

    def get_states(self):
        return {"x_outlier_pos": self.x_outlier_pos, "y_outlier_pos": self.y_outlier_pos, "z_outlier_pos": self.z_outlier_pos}

    def __get_all_states__(self):
        print( vars( self ) )

