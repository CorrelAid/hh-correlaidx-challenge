# Background to correlaidx-challenge-hh

- ...

# Notes on the interactive map

- The interactive map displays a standardized and normalized average across all features selected via the checkboxes
- Features include information with some relation to child wellbeing and are intended to be selected according to the user's specific information interest
- The combination of features is up to the user and the interpretation needs to be made with caution. The data has not been weighted and some factors may be over-, under- or misrepresented
- Features like "population" are included for illustration purposes, even though they are not directly linked to child wellbeing

# Instructions for running the interactive map

- Clone the repository to your local file system
- Set up an environment based on the included .yml file (e.g. by importing it to Anaconda or manually installing the libraries listed in the requirements file)
- Run the Dash_Map.py file in the terminal or via any IDE (e.g PyCharm)
- Open the web application via the provided localhost URL (e.g. http://127.0.0.1:8050/)

To add new datasets to the map: Place the file in pickle format in the folder "data_pickles" and the app will include it in the next run
