# newsfeedback

<img align="left" src="https://user-images.githubusercontent.com/102800020/225603245-b1dfdda6-bbe2-4c13-aec2-0a10ff26e231.png" width="150"> 


Tool for extracting and saving news article metadata at regular intervals. It utilizes [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/), [trafilatura ](https://github.com/adbar/trafilatura) and [Selenium](https://www.selenium.dev/) to extract and, if desired, filter article metadata across three different pipelines depending on a site's structure.
<p>
<b>Note: 🏗 This tool and its README are currently under construction 🏗</b>
<p> <br> <p>

## 💻 Installation and Usage

1. Install `poetry` if you don't have it: `pipx install poetry`.
2. Clone this repo, go into the repo's folder.
3. Install the dependencies with `poetry install` and spawn a shell in your new virtual environment with `poetry shell`.
3. To run tests type `pytest`, to try newsfeedback run `newsfeedback --help`.   

## 📰 Getting Started - Default

Note: "Out the box", newsfeedback retrieves a list of homepages to be extracted from the [default homepage config file](https://github.com/Leibniz-HBI/newsfeedback/blob/main/newsfeedback/defaults/default_homepage_config.yaml). It is recommended to proceed with extracting metadata with these unchanged settings once to get acquainted with the functionalities of the tool. 

1. After spawning `poetry shell`, proceed to run `newsfeedback pipeline-picker -u '[LINK OF YOUR CHOICE]'`. This URL **must** be in the config file. 
2. Check the output folder (default: newsfeedback/output) for the csv - this will be the structure of your exported CSVs.
3. If satisfied, proceed to run `newsfeedback get-data`, adding `-t [INTEGER]` to specify every `-t` newsfeedback is to grab data. This defaults to every 6 hours.

## 🎨 Customizing your parameters

### What are the different extraction and filtering pipelines newsfeedback offers?
<b>beautifulsoup</b> : using Beautiful Soup 4, URLs are extracted from the homepage HTML. As this initial URL collection is very broad, subsequent filtering is recommended. This is the most comprehensive pipeline for URL collection, but also has a higher quota of irrelevant URLs, especially if filtering is not turned on.
<ul>
<li> high URL success retrieval rates
<li> high rates of irrelevant URLs
<li> filtering recommended
</ul>
<b>trafilatura</b> : using trafilatura, articles are extracted from the given homepage URL. Success rates depend on the homepage HTML structure, but the quota of irrelevant URLs is very low.
<ul>
<li> URL retrieval success depends on homepage HTML structure
<li> low rates of irrelevant URLs
<li> filtering is not needed
</ul>
<b>purabo</b> : if a news portal requires access via a Pur Abo/data tracking consent (i.e. ZEIT online or heise), the consent button for the latter must be clicked via Selenium so that the article URLs can be collected. The Pur-Abo-pipeline continues with the same functionalities as the beautifulsoup-pipeline once the consent button has been clicked. <b>Note: oftentimes, article URLs can still be retrieved, as the page is loaded behind the overlay, so only use this pipeline if others fail.</b>
<ul>
<li> only needed for very few homepages
<li> dependant on Selenium and Beautiful Soup pipeline
<li> high rates of irrelevant URLs
<li> filtering recommended
</ul>


newsfeedback's filters are based on a simple whitelist with the eventual goal of allowing user additions to the whitelist rules. <b> Filters apply to URLs only </b>.  

Once article URLs have been extracted and, if need be, filtered, metadata is extracted with [trafilatura.bare_extraction](https://trafilatura.readthedocs.io/en/latest/corefunctions.html#bare-extraction). 

### I want to collect article metadata from a homepage that is not in the default homepage config file.
If you wish to generate a custom config file, run `newsfeedback add-homepage-url` and follow the instructions. You will be asked for the URL, the desired pipeline (either *beautifulsoup*, *trafilatura* or *purabo*)
<p> Note: This will spawn an empty user config, adding in the desired URL. <p> If you wish to extract metadata from the default homepages as well, please run `newsfeedback copy-homepage-config ` . newsfeedback will automatically refer to the user-generated config as the standard config for data collection.

### I want to collect different metadata than defined in the default metadata config file (title, url, description, date).
[WIP]

## 🗂 Commands

`newsfeedback --help` 
<p>Get an overview of the command line commands.

`newsfeedback add-homepage-url`
<p>Add a homepage URL to your config file (and thus to your metadata extraction workflow) via prompt.

`newsfeedback generate-config`
<p>Generate a new user config. Prompts the user to select either metadata or homepage as type of config and then clones the default settings into the new user config file. <p><b> If a user-generated homepage config already exists, newsfeedback will copy missing default homepage URLs into the user-generated config file. <p>
If a user-generated metadata config already exists, the users will be met with an error and prompted to adjust settings manually in the config, if so desired.</b>

`newsfeedback pipeline-picker` `-u` -> URL of the website you wish to extract metadata from. `-o` -> output folder (default: newsfeedback/output)
<p>Extracts article links and metadata from a homepage that is stored in the config file. A typical usecase is a trial run for the extraction of data from a newly added homepage.

`newsfeedback get-data` newsfeedback extracts the metadata and links once every `-t` (default: 6) hours.
<p>Using the homepages listed in the user config file (or the default config file, should the former not exist), metadata is extracted.

---

[Rahel Winter and Felix Victor Münch](mailto:r.winter@leibniz-hbi.de, f.muench@leibniz-hbi.de) under MIT.
