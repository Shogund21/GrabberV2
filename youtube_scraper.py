import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
import os
import webbrowser
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import json
import re
import threading
import csv
import pickle
import pandas as pd
from visualization import display_trending_chart


class YouTubeScraperApp:
    def __init__(self, master):
        self.master = master
        self.master.title("YouTube Video Scraper")
        self.master.geometry("800x600")

        self.style = ttk.Style()

        self.api_key = self.load_api_key()
        self.youtube = None
        if self.api_key:
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)

        self.use_api_var = tk.BooleanVar()
        self.use_api_var.set(bool(self.api_key))

        self.cache = self.load_cache()
        self.create_widgets()
        self.set_light_mode()  # Set light mode by default

    def load_api_key(self):
        try:
            with open('youtube_api_key.txt', 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return None

    def save_api_key(self, api_key):
        with open('youtube_api_key.txt', 'w') as f:
            f.write(api_key)

    def load_cache(self):
        try:
            with open('search_cache.pkl', 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return {}

    def save_cache(self):
        with open('search_cache.pkl', 'wb') as f:
            pickle.dump(self.cache, f)

    def get_api_key(self):
        api_key = simpledialog.askstring("YouTube API Key",
                                         "Please enter your YouTube API Key:",
                                         show='*')
        if api_key:
            self.save_api_key(api_key)
        return api_key

    def create_widgets(self):
        self.frame = ttk.Frame(self.master, padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(self.frame, text="Topic:").grid(column=0, row=0, sticky=tk.W)
        self.topic_entry = tk.Entry(self.frame, width=40)  # Changed to tk.Entry
        self.topic_entry.grid(column=1, row=0, sticky=(tk.W, tk.E))

        ttk.Label(self.frame, text="Days ago:").grid(column=0, row=1, sticky=tk.W)
        self.days_entry = tk.Entry(self.frame, width=10)  # Changed to tk.Entry
        self.days_entry.grid(column=1, row=1, sticky=(tk.W, tk.E))
        self.days_entry.insert(0, "30")  # Default value

        ttk.Label(self.frame, text="Max Results:").grid(column=0, row=2, sticky=tk.W)
        self.results_entry = tk.Entry(self.frame, width=10)  # Changed to tk.Entry
        self.results_entry.grid(column=1, row=2, sticky=(tk.W, tk.E))
        self.results_entry.insert(0, "10")  # Default value

        ttk.Label(self.frame, text="Country:").grid(column=0, row=3, sticky=tk.W)
        self.country_var = tk.StringVar()
        self.country_combobox = ttk.Combobox(self.frame, textvariable=self.country_var)
        self.country_combobox['values'] = ('US', 'GB', 'CA', 'DE', 'FR', 'JP', 'KR')  # Add more country codes as needed
        self.country_combobox.grid(column=1, row=3, sticky=(tk.W, tk.E))

        ttk.Label(self.frame, text="Category:").grid(column=0, row=4, sticky=tk.W)
        self.category_var = tk.StringVar()
        self.category_combobox = ttk.Combobox(self.frame, textvariable=self.category_var)
        self.category_combobox['values'] = ('All', 'Music', 'Gaming', 'News', 'Sports')  # Add more categories as needed
        self.category_combobox.grid(column=1, row=4, sticky=(tk.W, tk.E))

        self.search_button = ttk.Button(self.frame, text="Search", command=self.start_search)
        self.search_button.grid(column=1, row=5, sticky=tk.E)

        self.results = tk.Text(self.frame, wrap=tk.WORD, width=80, height=20)
        self.results.grid(column=0, row=6, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.results.yview)
        self.scrollbar.grid(column=2, row=6, sticky=(tk.N, tk.S))
        self.results['yscrollcommand'] = self.scrollbar.set

        self.progress_bar = ttk.Progressbar(self.frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.progress_bar.grid(column=0, row=7, columnspan=2, sticky=(tk.W, tk.E))

        self.status_label = ttk.Label(self.frame, text="")
        self.status_label.grid(column=0, row=8, columnspan=2, sticky=(tk.W, tk.E))

        self.use_api_checkbox = ttk.Checkbutton(self.frame, text="Use API Key",
                                                variable=self.use_api_var,
                                                command=self.toggle_api_use)
        self.use_api_checkbox.grid(column=0, row=9, sticky=tk.W)

        self.save_button = ttk.Button(self.frame, text="Save Results", command=self.save_results)
        self.save_button.grid(column=1, row=9, sticky=tk.W)

        self.change_api_button = ttk.Button(self.frame, text="Change API Key", command=self.change_api_key)
        self.change_api_button.grid(column=1, row=9, sticky=tk.E)

        self.trending_button = ttk.Button(self.frame, text="Get Trending", command=self.start_trending_search)
        self.trending_button.grid(column=0, row=10, sticky=tk.W)

        self.clear_button = ttk.Button(self.frame, text="Clear Screen", command=self.clear_screen)
        self.clear_button.grid(column=1, row=10, sticky=tk.E)

        self.view_chart_button = ttk.Button(self.frame, text="View Chart", command=self.view_chart)
        self.view_chart_button.grid(column=0, row=11, sticky=tk.W)

        self.export_button = ttk.Button(self.frame, text="Export Trending Data to CSV",
                                        command=self.export_trending_data_to_csv)
        self.export_button.grid(column=1, row=11, sticky=tk.E)

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(6, weight=1)

    def toggle_api_use(self):
        if self.use_api_var.get() and not self.api_key:
            self.change_api_key()
        elif not self.use_api_var.get():
            messagebox.showinfo("API Key Disabled", "You're now using the application without an API key.")

    def change_api_key(self):
        new_api_key = self.get_api_key()
        if new_api_key:
            self.api_key = new_api_key
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            self.use_api_var.set(True)
            messagebox.showinfo("Success", "API Key updated successfully.")
        else:
            self.api_key = None
            self.youtube = None
            self.use_api_var.set(False)
            messagebox.showinfo("API Key Removed", "You're now using the application without an API key.")

    def start_search(self):
        threading.Thread(target=self.search_videos, daemon=True).start()

    def search_videos(self):
        topic = self.topic_entry.get()
        days_ago = int(self.days_entry.get())
        max_results = int(self.results_entry.get())

        self.results.delete('1.0', tk.END)
        self.progress_bar['value'] = 0
        self.status_label.config(text="Searching...")
        self.master.update()

        cache_key = f"{topic}_{days_ago}_{max_results}"
        cached_results = self.cache.get(cache_key)

        if cached_results:
            self.display_results(cached_results)
            self.status_label.config(text="Results loaded from cache")
            return

        try:
            if self.use_api_var.get() and self.api_key:
                videos = self.get_recent_videos_by_topic_api(topic, days_ago, max_results)
            else:
                videos = self.scrape_youtube_search(topic, max_results)

            if not videos:
                self.status_label.config(text="No videos found")
                return

            # Sort videos by date, most recent first
            videos.sort(key=lambda x: self.parse_date(x['date']), reverse=True)

            self.cache[cache_key] = videos
            self.save_cache()

            self.display_results(videos)

        except HttpError as e:
            if e.resp.status == 403:
                messagebox.showerror("API Error", "API quota exceeded or invalid API key.")
            elif e.resp.status == 404:
                messagebox.showerror("API Error", "Requested resource not found.")
            else:
                messagebox.showerror("API Error", f"An API error occurred: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            self.status_label.config(text="Search failed")

    def display_results(self, videos):
        self.results.delete('1.0', tk.END)
        for i, video in enumerate(videos):
            self.results.insert(tk.END, f"Name: {video['name']}\n")
            self.results.insert(tk.END, f"Date: {video['date']}\n")
            self.results.insert(tk.END, f"Video ID: {video['video_id']}\n")

            if self.use_api_var.get() and self.api_key:
                analytics = self.get_video_analytics(video['video_id'])
                self.results.insert(tk.END, f"Views: {analytics['views']}\n")
                self.results.insert(tk.END, f"Likes: {analytics['likes']}\n")
                self.results.insert(tk.END, f"Comments: {analytics['comments']}\n")
            else:
                info = self.get_video_info_scrape(video['video_id'])
                self.results.insert(tk.END, f"Views: {info['views']}\n")

            view_button = ttk.Button(self.results, text="View Video",
                                     command=lambda v=video['video_id']: self.view_specific_video(v))
            self.results.window_create(tk.END, window=view_button)
            self.results.insert(tk.END, "\n---\n")

            self.progress_bar['value'] = (i + 1) / len(videos) * 100
            self.master.update_idletasks()

        self.status_label.config(text=f"Found {len(videos)} videos")

    def get_recent_videos_by_topic_api(self, topic, days_ago, max_results):
        start_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%dT%H:%M:%SZ')
        search_response = self.youtube.search().list(
            q=topic,
            type='video',
            part='id,snippet',
            order='date',
            publishedAfter=start_date,
            maxResults=max_results
        ).execute()

        videos = []
        for item in search_response['items']:
            video = {
                'name': item['snippet']['title'],
                'date': item['snippet']['publishedAt'],
                'video_id': item['id']['videoId']
            }
            videos.append(video)
        return videos

    def scrape_youtube_search(self, query, max_results=10):
        search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        response = requests.get(search_url)
        script = re.search(r"var ytInitialData = ({.*?});", response.text).group(1)
        data = json.loads(script)

        videos = []
        items = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
        for item in items:
            if 'videoRenderer' in item.keys():
                video_data = item['videoRenderer']
                title = video_data['title']['runs'][0]['text']
                video_id = video_data['videoId']
                try:
                    publish_date = video_data['publishedTimeText']['simpleText']
                    publish_date = self.convert_relative_date(publish_date)
                except KeyError:
                    publish_date = "1900-01-01T00:00:00Z"

                videos.append({
                    'name': title,
                    'video_id': video_id,
                    'date': publish_date
                })

                if len(videos) >= max_results:
                    break

        return videos

    def convert_relative_date(self, relative_date):
        current_date = datetime.now()
        if 'minute' in relative_date or 'hour' in relative_date:
            return current_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        elif 'day' in relative_date:
            days = int(relative_date.split()[0])
            date = current_date - timedelta(days=days)
            return date.strftime('%Y-%m-%dT%H:%M:%SZ')
        elif 'week' in relative_date:
            weeks = int(relative_date.split()[0])
            date = current_date - timedelta(weeks=weeks)
            return date.strftime('%Y-%m-%dT%H:%M:%SZ')
        elif 'month' in relative_date:
            months = int(relative_date.split()[0])
            date = current_date - timedelta(days=months * 30)  # Approximate
            return date.strftime('%Y-%m-%dT%H:%M:%SZ')
        elif 'year' in relative_date:
            years = int(relative_date.split()[0])
            date = current_date.replace(year=current_date.year - years)
            return date.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            return "1900-01-01T00:00:00Z"  # Default to very old date if format is unknown

    def parse_date(self, date_string):
        try:
            return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            return datetime(1900, 1, 1)

    def get_video_analytics(self, video_id):
        try:
            video_response = self.youtube.videos().list(
                part='statistics',
                id=video_id
            ).execute()

            stats = video_response['items'][0]['statistics']
            views = stats.get('viewCount', '0')
            likes = stats.get('likeCount', '0')
            comments = stats.get('commentCount', '0')

            return {
                'views': views,
                'likes': likes,
                'comments': comments
            }
        except HttpError as e:
            messagebox.showerror("API Error", f"An API error occurred: {e}")
            return {
                'views': 'N/A',
                'likes': 'N/A',
                'comments': 'N/A'
            }
        except KeyError as e:
            messagebox.showerror("API Error", f"Missing expected data: {e}")
            return {
                'views': 'N/A',
                'likes': 'N/A',
                'comments': 'N/A'
            }

    def get_video_info_scrape(self, video_id):
        url = f"https://www.youtube.com/watch?v={video_id}"
        response = requests.get(url)
        script = re.search(r"var ytInitialData = ({.*?});", response.text).group(1)
        data = json.loads(script)

        try:
            video_data = data['contents']['twoColumnWatchNextResults']['results']['results']['contents'][0][
                'videoPrimaryInfoRenderer']
            title = video_data['title']['runs'][0]['text']
            view_count_renderer = video_data.get('viewCount', {}).get('videoViewCountRenderer', {})
            views = view_count_renderer.get('viewCount', {}).get('simpleText', 'N/A')
            return {'title': title, 'views': views}
        except KeyError as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
            return {'title': 'N/A', 'views': 'N/A'}

    def view_specific_video(self, video_id):
        webbrowser.open(f"https://www.youtube.com/watch?v={video_id}")

    def save_results(self):
        content = self.results.get('1.0', tk.END)
        if content.strip() == "":
            messagebox.showinfo("Info", "No results to save")
            return

        file_types = [
            ("All Files", "*.*"),
            ("CSV Files", "*.csv"),
            ("JSON Files", "*.json"),
            ("Excel Files", "*.xlsx")
        ]
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=file_types)

        if not file_path:
            return

        try:
            if file_path.endswith(".csv"):
                self.save_as_csv(file_path)
            elif file_path.endswith(".json"):
                self.save_as_json(file_path)
            elif file_path.endswith(".xlsx"):
                self.save_as_excel(file_path)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            messagebox.showinfo("Success", f"Results saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving results: {e}")

    def save_as_csv(self, file_path):
        videos = self.parse_results_to_dict()
        keys = videos[0].keys()
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, keys)
            dict_writer.writeheader()
            dict_writer.writerows(videos)

    def save_as_json(self, file_path):
        videos = self.parse_results_to_dict()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(videos, f, ensure_ascii=False, indent=4)

    def save_as_excel(self, file_path):
        videos = self.parse_results_to_dict()
        df = pd.DataFrame(videos)
        df.to_excel(file_path, index=False)

    def parse_results_to_dict(self):
        lines = self.results.get('1.0', tk.END).strip().split("\n---\n")
        videos = []
        for line in lines:
            video = {}
            for detail in line.split("\n"):
                if detail.startswith("Name: "):
                    video['name'] = detail.replace("Name: ", "")
                elif detail.startswith("Date: "):
                    video['date'] = detail.replace("Date: ", "")
                elif detail.startswith("Video ID: "):
                    video['video_id'] = detail.replace("Video ID: ", "")
                elif detail.startswith("Views: "):
                    video['views'] = detail.replace("Views: ", "")
                elif detail.startswith("Likes: "):
                    video['likes'] = detail.replace("Likes: ", "")
                elif detail.startswith("Comments: "):
                    video['comments'] = detail.replace("Comments: ", "")
            videos.append(video)
        return videos

    def clear_screen(self):
        self.results.delete('1.0', tk.END)
        self.progress_bar['value'] = 0
        self.status_label.config(text="")

    def start_trending_search(self):
        threading.Thread(target=self.search_trending_videos, daemon=True).start()

    def search_trending_videos(self):
        country = self.country_var.get()
        category = self.category_var.get()

        self.results.delete('1.0', tk.END)
        self.progress_bar['value'] = 0
        self.status_label.config(text="Fetching trending videos...")
        self.master.update()

        try:
            if self.use_api_var.get() and self.api_key:
                self.trending_videos = self.get_trending_videos_api(country, category)
            else:
                self.trending_videos = self.scrape_trending_videos(country, category)

            if not self.trending_videos:
                self.status_label.config(text="No trending videos found")
                return

            # Sort videos by date, most recent first
            self.trending_videos.sort(key=lambda x: self.parse_date(x['date']), reverse=True)

            self.display_results(self.trending_videos)

        except HttpError as e:
            if e.resp.status == 403:
                messagebox.showerror("API Error", "API quota exceeded or invalid API key.")
            elif e.resp.status == 404:
                messagebox.showerror("API Error", "Requested resource not found.")
            else:
                messagebox.showerror("API Error", f"An API error occurred: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            self.status_label.config(text="Search failed")

    def get_trending_videos_api(self, country, category):
        if not country:
            country = 'US'  # Default to US if no country is selected

        video_category_id = self.get_category_id(category) if category != 'All' else ''

        try:
            search_response = self.youtube.videos().list(
                part='id,snippet,statistics',
                chart='mostPopular',
                regionCode=country,
                videoCategoryId=video_category_id if video_category_id else None,
                maxResults=50
            ).execute()

            videos = []
            for item in search_response['items']:
                video = {
                    'name': item['snippet']['title'],
                    'date': item['snippet']['publishedAt'],
                    'video_id': item['id'],
                    'views': item['statistics']['viewCount']
                }
                videos.append(video)
            return videos

        except HttpError as e:
            messagebox.showerror("API Error", f"An API error occurred: {e}")
            return []

    def scrape_trending_videos(self, country, category):
        # Implement scraping logic for trending videos if not using API
        # This function can be expanded to include more robust scraping techniques
        return []

    def get_category_id(self, category):
        # YouTube API category IDs
        categories = {
            'Film & Animation': '1',
            'Autos & Vehicles': '2',
            'Music': '10',
            'Pets & Animals': '15',
            'Sports': '17',
            'Short Movies': '18',
            'Travel & Events': '19',
            'Gaming': '20',
            'Videoblogging': '21',
            'People & Blogs': '22',
            'Comedy': '23',
            'Entertainment': '24',
            'News & Politics': '25',
            'Howto & Style': '26',
            'Education': '27',
            'Science & Technology': '28',
            'Nonprofits & Activism': '29',
            'Movies': '30',
            'Anime/Animation': '31',
            'Action/Adventure': '32',
            'Classics': '33',
            'Comedy': '34',
            'Documentary': '35',
            'Drama': '36',
            'Family': '37',
            'Foreign': '38',
            'Horror': '39',
            'Sci-Fi/Fantasy': '40',
            'Thriller': '41',
            'Shorts': '42',
            'Shows': '43',
            'Trailers': '44'
        }
        return categories.get(category, '')

    def view_chart(self):
        if not hasattr(self, 'trending_videos') or not self.trending_videos:
            messagebox.showinfo("Info", "No trending data to display")
            return

        display_trending_chart(self.trending_videos)

    def export_trending_data_to_csv(self):
        if not hasattr(self, 'trending_videos') or not self.trending_videos:
            messagebox.showinfo("Info", "No trending data to export")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "Views", "Date", "Video ID"])
                for video in self.trending_videos:
                    writer.writerow([video['name'], video['views'], video['date'], video['video_id']])
            messagebox.showinfo("Success", f"Trending data exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while exporting data: {e}")

    def set_light_mode(self):
        self.style.configure('TFrame', background='white')
        self.style.configure('TLabel', background='white', foreground='black')
        self.style.configure('TButton', background='white', foreground='black')
        self.style.configure('TEntry', fieldbackground='white', foreground='black')
        self.style.configure('TCombobox', fieldbackground='white', foreground='black')
        self.style.configure('TCheckbutton', background='white', foreground='black')
        self.style.configure('TScrollbar', background='white')

        self.results.config(bg='white', fg='black', insertbackground='black')
        self.master.config(bg='white')
        self.frame.config(style='TFrame')

        # Explicitly set foreground for tk widgets
        self.topic_entry.config(fg='black', bg='white')
        self.days_entry.config(fg='black', bg='white')
        self.results_entry.config(fg='black', bg='white')
        self.country_combobox.config(foreground='black', background='white')
        self.category_combobox.config(foreground='black', background='white')
        self.use_api_checkbox.config(style='TCheckbutton')


if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeScraperApp(root)
    root.mainloop()
