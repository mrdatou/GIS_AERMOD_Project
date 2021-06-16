import logging

from ui import MainWindow

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info('Start GIS To AERMOD Tool')

    root = MainWindow()

    root.mainloop()

    logging.info('Finish GIS To AERMOD Tool')