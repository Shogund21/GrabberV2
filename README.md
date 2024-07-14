#YouTube Video Scraper Application
Overview:
The YouTube Video Scraper application is a tool designed to help users search for and analyze YouTube videos based on specific topics, timeframes, and other parameters. This desktop application, built using Python and the Tkinter library, provides a graphical user interface (GUI) for users to input search criteria and view results.

Features:

Search Functionality:

Topic-Based Search: Users can search for videos by entering a topic or keyword.
Timeframe: The application allows users to specify the number of days to look back for video uploads.
Result Limitation: Users can limit the maximum number of search results.
Advanced Filters:

Country Filter: Users can filter search results based on country-specific YouTube domains.
Category Filter: Users can select specific video categories (e.g., Music, Gaming, News, Sports) to refine their search.
YouTube API Integration:

API Key Usage: The application uses the YouTube Data API for searching and retrieving video analytics. Users can provide their API key to enable this functionality.
Analytics: When using the API, the application can retrieve detailed video statistics such as views, likes, and comments.
Web Scraping:

Fallback Mechanism: If the API is not used, the application can scrape YouTube search results to provide basic video information.
Data Management:

Caching: Search results are cached to improve performance and reduce redundant API calls.
Save Results: Users can save search results in various formats, including CSV, JSON, and Excel.
Export Trending Data: Users can export trending video data to a CSV file.
Visualization:

Trending Videos: The application can fetch and display trending videos for specific countries and categories.
Charts: Users can view charts of the trending videos' data for better analysis.
User Interface:

Light Mode: The application is set to light mode by default, providing a clean and user-friendly interface.
Responsive Design: The GUI is designed to be responsive and easy to navigate.
Usage:

Search Videos:

Enter a topic in the "Topic" field.
Specify the number of days to look back in the "Days ago" field.
Set the maximum number of results in the "Max Results" field.
Optionally, select a country and category.
Click the "Search" button to fetch and display results.
Trending Videos:

Select a country and category.
Click the "Get Trending" button to fetch trending videos.
View and Save Results:

View detailed video information in the results area.
Click the "Save Results" button to save data in the desired format.
Use the "Export Trending Data to CSV" button to export trending video data.
Configuration:

Click "Change API Key" to enter or update your YouTube API key.
Use the "Use API Key" checkbox to toggle between using the API and web scraping.
Dependencies:

Python libraries: tkinter, googleapiclient, requests, BeautifulSoup, json, re, threading, csv, pickle, pandas
External modules: visualization (for displaying charts)
Installation:

Install Python and necessary libraries.
bash
Copy code
pip install google-api-python-client requests beautifulsoup4 pandas
Run the application script.
bash
Copy code
python youtube_scraper.py
Executable Creation:
To create an executable file for the application, use PyInstaller:

bash
Copy code
pip install pyinstaller
pyinstaller --onefile youtube_scraper.py
The executable will be located in the dist directory.

Conclusion:
The YouTube Video Scraper application provides a powerful and user-friendly interface for searching and analyzing YouTube videos. With features like topic-based search, advanced filtering, API integration, data caching, and exporting capabilities, it is a versatile tool for researchers, marketers, and content creators.
