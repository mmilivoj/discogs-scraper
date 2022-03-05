# Discogs Scraper
Find best deal for a specific vinyl (long-playing record) on Discogs.

### What does <ins>best</ins> mean?

<img src="https://latex.codecogs.com/svg.latex?\Large&space;Best Deal=\frac{Media Condition\times(\frac{Want}{Have})}{Total Price}" title="\Large x=\frac{-b\pm\sqrt{b^2-4ac}}{2a}" />

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
## Installation
- 
## Example
* Searching with album title only
  * ...
* Searching with a specified artist or band 
  * ...
* 