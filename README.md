# 🍻 Truth behind ratings 🍻

##  📄 Abstract

The core of the project is the idea of exploring the influence of various factors on the ratings left by users, so as to gain a better understanding of the final ratings we can consult by visiting Beer Advocate or Rate Beer. In other words, what secrets do the ratings conceal? The goal of the project is therefore to identify several factors that may affect reviews, and to test our hypotheses against the data.

The motivation behind the project came from an informal discussion within the team about our disagreements over the ratings of certain movies. When it came time to come up with an idea for the project, we wanted to transpose our thoughts on the film question onto beer reviews. Let's embark on an adventure and find out as we go along that the ratings you use to pick your next beer may not be so truthful after all!

<img src="src/data/meme.jpg" width="400px"/>

## 🔍 Research Questions

The questions we intend to answer concern various factors that could influence ratings.

1. How can we quantify users' knowledge of beer and what's the impact on the ratings ?
2. How can the preferences of the users impact the ratings on the websites ?
3. Are text reviews and user scores consistent with each other across regions?
4. Are users influenced by the past rating of the beer ?
    -  Inconclusive after work done for P3
5. Are users influenced by their past ratings ?
    -  Inconclusive after work done for P3
6. Are users influenced by current trends in beer consumption ? 
    -  Inconclusive after work done for P3

## 📦 Additional datasets

Our datasets are composed on information from two websites,  BeerAdvocate and RateBeer. Current review data ranges from August 1996 to August 2017 for BeerAdvocate and April 2000 to August 2017 for RateBeer. 

We thought of developing a scraper to retrieve more recent data from August 2017 to today. Nevertheless, after a preliminary analysis, we encountered some technical pitfalls. Indeed, the websites require users to be authenticated to consult reviews, and maybe impose a rate limit on queries, which could complicate information retrieval.
## 🎛️ Methods

Our analyses will attempt to answer the questions presented above, and for questions 2 to 5, they will also be carried out on different segments of users and beers such as the user's country, knowledge of beers, country of the beer, style of beer, etc. 

All our analyses will be conducted separately on the data from each website, and the results will be compared to determine whether they are consistent across the two websites.



### 1. How can we quantify users' knowledge of beer and what's the impact on the ratings ?

We tried to use different features and combination of features to derive a notion of beer knowledge for each user at different points in time.

We defined our own expressions of local and global knowledge based on the number of beers rated at a given time relatively to the number of beers available at that time.

To assess the impact of this knowledge on the ratings we defined two test groups of users : novices with low knowledge and experts with high knowledge. We then performed t-test and F-tests to assess the difference between their ratings and then measured them.

### 2. How can the preferences of the users impact the ratings on the websites ?

In order to analyze how preferences, in the sense of the number of beers rated, can influence scores, we carried out matchings between style pairs. For each style, we defined a group of users whose most-rated style is this one, then observed how they rated the other styles in relation to their average across all styles.

### 3. Are text reviews and user scores consistent with each other across regions?

In order to compare the similarity of textual reviews and ratings, we used the NLP model ⁠ nlptown/bert-base-multilingual-uncased-sentiment ⁠ [^1] for sentiment analysis. More specifically, the model predicts the sentiment of a review as an integer in $[1,5]$ which corresponds to the same range as the scores given by the users. We then compared the deviation of predicted ratings to actual ratings and assessed the difference conditionned on the region
of the users using ANOVA and Tukey pair-wise tests.

### 4. & 5. Are we influenced by our past ratings and the past rating of the beer ? 
    -  Inconclusive after work done for P3, planned method only

We believe that the effects of these 2 hypotheses may be correlated, and we therefore plan to analyze their impact using a linear regression with the following parameters of interest :
- Average of this user's past ratings
- Average of the beer at the time of rating
- Interaction term for the joint effect

After preliminary analyses, we performed an F-test on the coefficient of the interaction term at the $\alpha=0.01$ threshold. The test concluded on the rejection of the null hypothesis, so it seems that the interaction of the 2 effects is statistically significant.

We will analyse the results of the linear regression in more details, and add other parameters to observe their effects (e.g. past average by beer style).

### 6. Are users influenced by current trends in beer consumption ?
    -  Inconclusive after work done for P3, planned method only

In order to analyze the impact of trends on scores, we first need to identify trends. We intend to use a hybrid approach:
- Manually identify trends via research on news sites and market studies
- Automatically identify trends by analyzing the number of ratings for a certain style of beer as a function of the number of active users.

We will define the active status of a user according to parameters such as his review rate, the date since his last review and other parameters.

Subsequently, we plan to use hypothesis tests such as the T-test to compare average ratings during trends and outside them. 

We also plan to use a linear regression model to estimate the impact of trends on averages compared with off-trend averages.

## 🗓️ Proposed Timeline

| Period | Description |
|---|---|
| Week 1 : 18/11 - 24/11 | <ul><li>Implementation of user beer knowledge metrics (1)</li><li>Data exploration on trend analysis (6)</li></ul> |
| Week 2 : 25/11 - 01/12 | <ul><li>Analysis of regression for effects (4) and (5) : more complex regresson, additional parameters</li><li>Use of knowledge metric to define experts (1)</li></ul> |
| Week 3 : 02/12 - 08/12 | <ul><li>Training and inference on text reviews to assess differences with ratings (3)</li><li>Identification of impact of beer preference for certain styles on other styles (2)</li></ul> |
| Week 4 : 09/12 - 15/12 | <ul><li>Finalizing analysis for each research questions</li><li>Beginning of data story website and report : choice of visulisations, building website's boilerplate</li></ul> |
| Week 5 : 16/12 - 20/12 | <ul><li>Finalize data story and report</li><li>Clean repository and verify all artefacts</li></ul> |

## 👥 Organization within the team

Our team consists of 2 members with a background in computer science and 3 with backgrounds in mathematics and physics. We will split the tasks to leverage each other's strengths while allowing all members to acquire new skills. 

Contributions:
- Jean : Data preprocessing handling large files, creating the final website, dealing with the research question on the impact of users' preferences
- Kilian : Analysing and interpreting plots during data exploration, handling NLP analysis, formatting every paragraph to assert consistency
- Léon : Analysing and interpreting plots during data exploration, finding the expression of knowledge, writing conclusion of data story, checking relevancy of others' analysis
- Arthur : Conducting preliminary analysis to select only relevant data for final analysis, writing introduction and interpretations for data story
- Martin : Finding the expression of knowledge, creating plots for data exploration, handling expert and novices analysis, formatting python scripts



## 📑 Instructions

Please download the datasets by folowing these commands :
```bash
cd src/scripts
python download.py
cd ../../
pip install -r pip_requirements.txt
```

## 🗄️ Project Structure

```
├── data                        <- Project data files
│
├── src                         <- Source code
│   ├── data                            <- Data directory
│   ├── models                          <- Model directory
│   ├── utils                           <- Utility directory
│   ├── scripts                         <- Shell scripts
│
│
├── milestone_2.ipynb               <- a well-structured notebook showing the results of data exploration for P2
├── milestone_3.ipynb                 <- a well-structured notebook showing our analysis for P3
│
├── .gitignore                  <- List of files ignored by git
├── pip_requirements.txt        <- File for installing python dependencies
└── README.md
```

## References

[^1]: NLP Town (2023). HugginFace - nlptown/bert-base-multilingual-uncased-sentiment. Available : https://huggingface.co/nlptown/bert-base-multilingual-uncased-sentiment
