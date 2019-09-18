
#  subs2network

Subs2net is a python package that converts srt subtitles into a social network of interaction between the movie characters.
This is an alpha version, additional refactoring and code cleanup are planned to improve usability and  simplicity.
 More details on the project can be find in the our paper titled ["Using Data Science to Understand the Film Industry's Gender Gap"](https://arxiv.org/abs/1903.064690)
 
 ## Installation
 ```
 pip install https://github.com/data4goodlab/subs2network/master
 ```
 ### Dev
```
git clone https://github.com/data4goodlab/subs2network.git
pipenv install
```

## Usage
```
from subs2network.consts import set_output_path
from subs2network.videos_sn_creator import generate_movie_graph
set_output_path("/My path")
generate_movie_graph("Movie Name", year, imdb_id)
```
If set_output_path is not defined, the generated graph will be saved at a def \Users\Your-User\\.subs2net\output\movies\Movie Name
