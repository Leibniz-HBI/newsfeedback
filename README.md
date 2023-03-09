# newsfeedback

<img align="left" src="https://user-images.githubusercontent.com/102800020/224003684-50226842-377f-4cab-a817-8c9502b43510.png" width="150"> 


Tool for extracting and saving news article metadata at regular intervals. It utilizes [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/), [trafilatura ](https://github.com/adbar/trafilatura) and [Selenium](https://www.selenium.dev/) to extract and, if desired, filter article metadata across three different pipelines depending on a site's structure.
<p>
<b>Note: 🏗 This tool and its README are currently under construction 🏗</b>
<p> <br> <p>

## Installation and Usage

1. Install `poetry` if you don't have it: `pipx install poetry`.
2. Clone this repo, go into the repo's folder.
3. Install the dependencies with `poetry install` and spawn a shell in your new virtual environment with `poetry shell`.
3. To run tests type `pytest`, to try newsfeedback run `newsfeedback --help`.   

## Getting Started - Default

Note: "Out the box", newsfeedback retrieves a list of homepages to be extracted from the [default homepage config file](https://github.com/Leibniz-HBI/newsfeedback/blob/main/newsfeedback/defaults/default_homepage_config.yaml). It is recommended to proceed with extracting metadata with these unchanged settings once to get acquainted with the functionalities of the tool. 

1. After spawning `poetry shell`, proceed to run `newsfeedback pipeline-picker -u '[LINK OF YOUR CHOICE]'`. This URL **must** be in the config file. 
2. Check the output folder (default: newsfeedback/output) for the csv - this will be the structure of your exported CSVs.
3. If satisfied, proceed to run `newsfeedback get-data`, adding `-t [INTEGER]` to specify every `-t` newsfeedback is to grab data. This defaults to every 6 hours.

## Customizing your parameters

### What are the different extraction and filtering pipelines newsfeedback offers?
<li> beautifulsoup : using the Beautiful Soup 
<li> trafilatura : 
<li> purabo :

### I want to collect article metadata from a homepage that is not in the default homepage config file.
If you wish to generate a custom config file, run `newsfeedback add-homepage-url` and follow the instructions. You will be asked for the URL, the desired pipeline (either *beautifulsoup*, *trafilatura* or *purabo*)
<p> Note: This will spawn an empty user config, adding in the desired URL. <p> If you wish to extract metadata from the default homepages as well, please run `newsfeedback copy-homepage-config`. newsfeedback will automatically refer to the user-generated config as the standard config for data collection.

### I want to collect different metadata than defined in the default metadata config file (title, url, description, date).
[WIP]

## Commands

`newsfeedback --help` 
<p>Get an overview of the command line commands.

`newsfeedback add-homepage-url`
<p>Add a homepage URL to your config file (and thus to your metadata extraction workflow) via prompt.

`newsfeedback copy-homepage-config`
<p>Reproduces the default homepage config and copies the entries into a user-generated config.

`newsfeedback pipeline-picker` - `-u` -> URL of the website you wish to extract metadata from. `-o` -> output folder (default: newsfeedback/output)
<p>Extracts article links and metadata from a homepage that is stored in the 

`newsfeedback get-data` - `-t` -> newsfeedback extracts the metadata and links once ever `-t` (default: 6) hours.
<p>Using the homepages listed in the user config file (or the default config file, should the former not exist), metadata is extracted

---

[Rahel Winter and Felix Victor Münch](mailto:r.winter@leibniz-hbi.de, f.muench@leibniz-hbi.de) under MIT.
