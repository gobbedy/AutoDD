## About autodd Rev 3

AutoDD = Automatically does the "due diligence" for you. 
If you want to know what stocks people are talking about on reddit, this little program might help you. 

Original author - Fufu Fang https://github.com/fangfufu

Rev 2 Authors - Steven Zhu https://github.com/kaito1410 Napo2k https://github.com/Napo2k

Rev 3 Author - Guillaume Perrault-Archambault https://github.com/gobbedy

The original AutoDD produced a simple table of the stock ticker and the number of threads talking about the ticker.

Version 2 of AutoDD adds some options and features that the original did not have.

	- ability to display a change in results (ie, an increase or decrease of score from the previous day to today)
	
	- ability to pull additional stock information from yahoo finance (such as open and close price, volume, average volume, etc)
	
	- ability to pull results from multiple subreddits (pennystocks, RobinHoodPennyStocks, stocks, Daytrading, etc)
	
	- added score system to calculate a score for each ticker based on the number of occurrences, DD, Catalyst, or technical analysis flair, and number of upvotes
	
	- Can be run with a windows scheduler to run the program at a set time everyday

Version 3 adds further options and improvements:

	- A speedup of roughly 20x (multi-threading + low-level yahoo API manipulation)

	- Ability to use proxies for further speedup (roughly proportional to the number of proxies)

    - Fix the reddit scores, using hybrid of psaw/praw

    - Add additional popular subreddits (wallstreetbetELITE, satoshistreetbets)

    - Improve the regex expression for finding tickers

    - Refactor the code (use pandas dataframes, object orientation)

## Requirements 

Python (tested on python 3.8.1) https://www.python.org/downloads/release/python-381/

psaw - pip install psaw https://pypi.org/project/psaw/

praw - pip install praw https://pypi.org/project/praw/

pandas - pip install tabulate https://pypi.org/project/pandas/

requests - pip install requests https://pypi.org/project/requests/

tabulate - pip install tabulate https://pypi.org/project/tabulate/

The requirements can be installed by running install_requirements.bat / install_requirements.sh

## Running

Watch the setup video here https://www.youtube.com/watch?v=YwfwJYjnBFU

To set up the dependencies on Windows 10

	1. Install python 3.8 and make sure you add python to the path variable during installation
	2. Run install_requirements.bat, it should open a terminal and install the dependencies
	3. If all dependencies are installed successfully, run run_auto_dd.bat
	4. After 1-2 minutes, you should find a table_records.txt file in the AutoDD folder
	5. To generate a new table, simply run run_auto_dd.bat again, it will append a new table to the table_records.txt file

To set up the dependencies on Linux/MacOSX
	
	1. Install python 3.8 and Pip3 https://medium.com/swlh/installing-python-and-pip-on-mac-72b7639a58
	2. Run install_requirements.sh, it should open a terminal and install the dependencies
	3. If all dependencies are installed successfully, run run_auto_dd.sh
	4. After 1-2 minutes, you should find a table_records.txt file in the AutoDD folder
	5. To generate a new table, simply run run_auto_dd.bat again, it will append a new table to the table_records.txt file


For Advanced Users:
	
	1. Simply open the terminal (powershell or command prompt on windows, terminal on linux/MacOSX) and navigate to the AutoDD folder, then type:
		
		python main.py -h
		
	2. Follow the help document and set up the optional parameters as you'd like. 

## Columns Explained

Code - Ticker Name

Total - Total score on the ticker for r/pennystock subreddit. Higher means more discussions/chatter about this ticker

Recent - Score of the ticker from the last X hours. By default, Recent shows the score from the last 12 hours. If you change the interval for example --interval 48, then recent show data from 24 hours ago (48 divide by 2)

Prev - Score of the ticker from the last X to 2X hour period. By default, Prev shows the score from the last 12-24 hour period. If you change the interval for example --interval 48, then recent show data from the 24-48 hour period

Change - (Recent score - Prev score) Shows increase or decrease in amount of chatter/discussions about this ticker. Positive numbers = increase in discussions, higher numbers means more discussions/chatter about this ticker

Rockets - Number of Rocket Emojis

Price - Current stock price

%DayChange - Percentage change in todays price compared to yesterday

%50DayChange - Percentage change in todays price compared to the last 50 day average

%ChangeVol - Percentage Change in volumn from today to the 3 month average

Float - Float shares, number of tradable shares of the ticker

Industry - Industry of the company if available

## Example output

Default Output:

![Alt text](img/default_table.JPG?raw=true "Title")

Allsub Option Output:

![Alt text](img/allsub_option.JPG?raw=true "Title")

Yahoo Option Output:

![Alt text](img/yahoo_option.JPG?raw=true "Title")

## Options

In terminal, type:

	python main.py -h
	
This will produce the following help text:

	usage: main.py [-h] [--interval [INTERVAL]] [--min [MIN]] [--adv] [--sub [SUB]] [--sort [SORT]] [--filename [FILENAME]]

	autodd Optional Parameters

	optional arguments:
	-h, --help            show this help message and exit
	--interval [INTERVAL]
							Choose a time interval in hours to filter the results, default is 24 hours
	--min [MIN]           Filter out results that have less than the min score, default is 10
	--yahoo               Using this parameter shows yahoo finance information on the ticker, makes the script run slower!
	--sub [SUB]           Choose a different subreddit to search for tickers in, default is pennystocks
	--sort [SORT]         Sort the results table by descending order of score, 1 = sort by total score, 2 = sort by recent score, 3 = sort by previous score, 4 = sort by change in score, 5 = sort by # of rocket emojis
	--csv                 Using this parameter produces a table_records.csv file, rather than a .txt file
	--filename [FILENAME]
							Change the file name from table_records.txt to whatever you wish
			
			
			
Interval (Time interval)

	1. Choose a time interval N in hours to filter the results, default is 24 hours
	
	2. The score in the Total column shows the score for each ticker in the last N hours
	
	3. The score in the Recent column shows the score for each ticker in the last N/2 hours, default to 12h
	
	4. The score in the Prev column shows the score for each ticker in the last N/2 - N hours, default is 12h - 24h
	
	5. The score in the other subreddit columns shows the score for each ticker in the last 24 hours
	
	
Min (Minimum score)

	1. Filter out results that have less than the min score in the Title column, default is 10
	
	
Advanced (Yahoo Finance toggle)

	1. Using this parameter shows yahoo finance information, running yahoo mode is slower
	
	2. This options shows additional yahoo information on the ticker, such as open price, day low, day high, forward PE, beta, volume, etc.
	
	
Sub (Subreddit Selection)

	1. Choose a different subreddit to search for tickers in, default is pennystocks
	
	2. When a different subreddit is choosen, the total, recent, prev columns contain the score for the choosen subreddit
	
	3. Possible choices: pennystocks, RobinHoodPennyStocks, Daytrading, StockMarket, stocks


Sort

	1. Sort the results by descending order of score, by default the table shows the highest total score first
	
	2.  pass in values 1, 2, 3, or 4
	
	3. 1 = sort by total score, 2 = sort by recent score, 3 = sort by previous score, 4 = sort by change in score, 5 = sort by change in # of rocket emojis

Csv 

	1. Outputs table_records.csv file

Filename

	1. choose a different filename, this programs saves the table results to table_records.txt in the same folder as the AutoDD.py program

