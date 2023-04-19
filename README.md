# newsfeedback

<img align="left" src="https://user-images.githubusercontent.com/102800020/225603245-b1dfdda6-bbe2-4c13-aec2-0a10ff26e231.png" width="150"> 

Tool for extracting and saving news article metadata at regular intervals. It utilizes [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/), [trafilatura ](https://github.com/adbar/trafilatura) and [Selenium](https://www.selenium.dev/) to extract and, if desired, filter article metadata across three different pipelines depending on a site's structure.
<p>
<b>Note: 🏗 This tool and its README are currently under construction 🏗</b>
<p> <br> <p>

## 💻 Installation and Usage

If you use `pipx`, you can install with `pipx install newsfeedback`. Alternatively, you can install via `pip`: `pip install newsfeedback`.
There you go! You can now run `newsfeedback --help` and the commands outlined below. To run tests type `pytest`.   

## 📦 Getting Started - Default

"Out the box", newsfeedback retrieves a list of homepages to be extracted from the [default homepage config file](https://github.com/Leibniz-HBI/newsfeedback/blob/main/newsfeedback/defaults/default_homepage_config.yaml). It is recommended to proceed with extracting metadata with these unchanged settings once to get acquainted with the functionalities of the tool. 

1. After installing `newsfeedback`, run `newsfeedback pipeline-picker -u '[LINK OF YOUR CHOICE]'`. This URL **must** be in the config file. 
2. Check the output folder (default: newsfeedback/output) for the csv - this will be the structure of your exported CSVs.
3. If satisfied, proceed to run `newsfeedback get-data`, adding `-t [INTEGER]` to specify every `-t` newsfeedback is to grab data. 
<p>Note: This defaults to every 6 hours and extracts data from <b>all</b> default homepage URLs in the config. If you wish to only extract data from one URL, add it to a custom config with `newsfeedback add-homepage-url` and then re-run Step 3.

## 💻 Running newsfeedback on a server

If you want to run newsfeedback on a dedicated server, please make sure that you have Chrome installed on said server. Otherwise, you may be met with a [Chrome binary error](https://github.com/SergeyPirogov/webdriver_manager/issues/372) when using the Pur Abo pipeline.

## 🗂 Commands

`newsfeedback --help` 
<p>Get an overview of the command line commands.

`newsfeedback add-homepage-url`
<p>Add a homepage URL to your config file (and thus to your metadata extraction workflow) via prompt.

`newsfeedback generate-config`
<p>Generate a new user config. Prompts the user to select either metadata or homepage as type of config and then clones the default settings into the new user config file. <p><b> If a user-generated homepage config already exists, </b>missing default homepage URLs will be copied into the user-generated config file. <p>
<b>If a user-generated metadata config already exists, </b>the users will be met with an error and prompted to adjust settings manually in the config.

`newsfeedback pipeline-picker` `-u` → URL of the website you wish to extract metadata from. `-o` → output folder (default: newsfeedback/output)
<p>Extracts article links and metadata from a homepage that is stored in the config file. A typical usecase is a trial run for the extraction of data from a newly added homepage.

`newsfeedback get-data` newsfeedback extracts the metadata and links once every `-t` (default: 6) hours.
<p>Using the homepages listed in the user config file (or the default config file, should the former not exist), metadata is extracted.

## 🎨 Customizing your parameters

### Extraction and filtering pipelines
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


<b> Filters apply to URLs only </b>.  newsfeedback's filters are based on a simple whitelist with the eventual goal of allowing user additions to the whitelist rules. Due to this tool still being in its infancy, these filters are far from sophisticated ☺

Once article URLs have been extracted and, if need be, filtered, metadata is extracted with [trafilatura.bare_extraction](https://trafilatura.readthedocs.io/en/latest/corefunctions.html#bare-extraction). 

### Adding data to the config file
If you wish to generate a custom config file, run `newsfeedback add-homepage-url` and follow the instructions. You will be asked for the URL, the desired pipeline (either *beautifulsoup*, *trafilatura* or *purabo*). <b> This will spawn an empty user config, adding in the desired URL. </b> If you wish to extract metadata from the default homepages as well, please run `newsfeedback generate-config` and select homepage, as this copies the missing URLs into the user-generated config. newsfeedback will automatically refer to the user-generated config, if present, as the standard config for data collection.

### Changing the types of metadata collected
By default, newsfeedback collects an article's `title, url, description, date`. If you wish to collect other categories of metadata, simply generate a user config file with `newsfeedback generate-config` and then manually adjust the settings within this file. Possible categories of metadata are: <i>title, author, url,  hostname, description, sitename, date, categories, tags, fingerprint, id, license, body, comments, commentsbody, raw_text, text, language</i>. Note that not all website may provide all categories.

---

[Rahel Winter and Felix Victor Münch](mailto:r.winter@leibniz-hbi.de, f.muench@leibniz-hbi.de) under MIT.
