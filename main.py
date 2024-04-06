from watchdog.events import FileSystemEvent, FileSystemEventHandler, DirCreatedEvent
from watchdog.observers import Observer
import pathlib
import datetime
import logging

class CFX96FileHandler(FileSystemEventHandler):
    def __init__(self, watched_path:str) -> None:
        super().__init__()
        self.watched_path = watched_path

    def on_created(self, event: FileSystemEvent) -> None:
        '''TO DO: Place all files not related to the CFX96 to a dir called 'GeneralMisc' '''
        date = datetime.datetime.now().date().strftime("%Y%m%d")
        file_created = pathlib.Path(event.src_path)

        if not len(file_created.name.split(" - ")) > 1:
            general_misc_dir = self.__create_general_misc_dir()
            self.__move_to__(general_misc_dir, file_created)
            return None
        
        daily_dir = self.__create_daily_dir__(date)
        run_dir = self.__create_run_dir__(file_created.name, daily_dir)
        misc_dir, results_dir = self.__create_inner_dirs__(run_dir)
        
        if file_created.name.find("Quantification Cq Results_0") > -1:
            self.__move_to__(results_dir, file_created)
        elif file_created.name.find("Quantification Amplification Results") > -1:
            self.__move_to__(results_dir, file_created)
        else:
            self.__move_to__(misc_dir, file_created)


    def __create_daily_dir__(self, new_dir:str) -> pathlib.Path:
        '''Makes the daily dir if it doesn't exist'''
        path = pathlib.Path(self.watched_path, new_dir)
        if path.exists(): return path
        path.mkdir()
        return path
    
    def __create_run_dir__(self, file_created:str, daily_dir:pathlib.Path)->pathlib.Path:
        '''Makes the run dir if it doesn't exist
            TO DO: Will be called for each file created and will check whether the run dir exists each time, make it check once
        '''
        run_title = file_created.split(" - ")[0]
        run_dir = daily_dir/run_title        
        if run_dir.exists(): return run_dir
        run_dir.mkdir()
        return run_dir
    
    def __create_inner_dirs__(self, run_dir:pathlib.Path)->tuple[pathlib.Path, pathlib.Path]:
        '''Creates a Misc dir and Results dir in the Run dir'''
        MISC = "Misc"
        RESULTS = "RawResults"

        misc_dir = run_dir/MISC
        results_dir = run_dir/RESULTS

        if not misc_dir.exists(): misc_dir.mkdir()
        if not results_dir.exists(): results_dir.mkdir()

        return (misc_dir, results_dir)

    def __move_to__(self, target_dir:pathlib.Path, file:pathlib.Path)->None:
        parent = target_dir.absolute()
        file_name = file.name
        #.DS_Store is a temporary file with the same name as the original file created by MacOS to save changes to temporarily... I believe
        if file_name.find(".DS_Store") > -1: return None   
        try:
            file.rename(parent/file_name)
            logger.info(f"Moved {file_name} to {target_dir.name}")
        except Exception as e:
            logger.error(f"File: {file_name} could not be moved to the correct directory here is the Python Error: ", e)

    def __create_general_misc_dir(self)->pathlib.Path:
        general_misc_dir = pathlib.Path(self.watched_path, "GeneralMisc")
        if general_misc_dir.exists(): return general_misc_dir
        general_misc_dir.mkdir()
        return general_misc_dir

class CFX96Observer():
    filepath = "."

    def __init__(self)->None:
        self.__observer__ = Observer()
        self.__observer__.schedule(CFX96FileHandler(self.filepath), self.filepath, recursive=False)

    def watch(self)->None:
        print("Started monitoring the CFX96 C1000 NAS filepath for exported runs")
        self.__observer__.start()
        self.__observer__.run()



def main()->None:
    observer = CFX96Observer()
    observer.watch()
    
if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename = "CFX96_FileWatcherLog.txt", encoding="utf-8", filemode="a", datefmt="%Y%m%d %H:%M:%S", level=logging.INFO, format="%(asctime)s %(message)s")
    main()