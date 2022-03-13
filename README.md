# Discogs Scraper
Finds best deal for a specific vinyl (long-playing record) on [Discogs](https://www.discogs.com/).

### What does <ins>best</ins> mean?

<img src="https://latex.codecogs.com/svg.latex?\Large&space;\color{green}BestDeal=\frac{MediaCondition\times(\frac{Want}{Have})}{TotalPrice}"></img>

The higher the BestDeal-quotient, the more valuable the deal.

All parameters are provided by the Discogs marketplace.

The **TotalPrice** is rendered based on your location, and consists of the price given by the seller and the shipping costs for your specific country. For example, in Germany the total price will be displayed in €.
  * The higher the total price the lower the quotient.

The **Want/Have** describes how many users want the vinyl, as how many users have the vinyl in their collection.
  * The higher the **Want/Have** ratio, the higher the quotient.

The **MediaCondition** is a converted value:
```
1.0 = Mint            
0.8 = Near Mint
0.6 = Very Good Plus
0.4 = Very Good
```
The higher the MediaCondition value, the higher the quotient.

### Installation and Usage
1. Clone the project into your desired directory.
    * ```git clone https://github.com/mmilivoj/discogs-scraper.git```
2. Navigate to the above mentioned directory.
3. Install [pipenv](https://pypi.org/project/pipenv/) if you have not already got it:
    * python3 -m pip install pipenv
3. Create pipenv: ```pipenv install```
4. Activate pipenv: ```pipenv shell```
    * Activated pipenv: ```(discogs-scarper) [...]$```
    * Exit pipenv environment by typing: ```exit```
5. Run script in pipenv: ```python3 scrape.py --album="[...]" --artist="[[...] Optional]"```
#### Example (within pipenv shell)
* Searching with album title only
  * ```python3 scrape.py --album="the dark side of the moon"```
* Searching with a specified artist or band 
  * ```python3 scrape.py --album="love" --artist="the cult"```
