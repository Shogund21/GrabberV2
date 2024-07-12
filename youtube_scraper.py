import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog, scrolledtext
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

class YouTubeScraperApp:
    def __init__(self, master):
        self.master = master
        self.master.title("YouTube Video Scraper")
        self.master.geometry("800x600")

        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.api_key = self.load_api_key()
        self.youtube = None
        if self.api_key:
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)

        self.use_api_var = tk.BooleanVar()
        self.use_api_var.set(bool(self.api_key))

        self.cache = self.load_cache()
        self.create_widgets()
        self.dark_mode = False

    def load_api_key(self):
        try:
            with open(os.path.join(self.base_path, 'youtube_api_key.txt'), 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return None

    def save_api_key(self, api_key):
        with open(os.path.join(self.base_path, 'youtube_api_key.txt'), 'w') as f:
            f.write(api_key)

    def load_cache(self):
        try:
            with open(os.path.join(self.base_path, 'search_cache.pkl'), 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return {}

    def save_cache(self):
        with open(os.path.join(self.base_path, 'search_cache.pkl'), 'wb') as f:
            pickle.dump(self.cache, f)

    def get_api_key(self):
        api_key = simpledialog.askstring("YouTube API Key",
                                         "Please enter your YouTube API Key:",
                                         show='*')
        if api_key:
            self.save_api_key(api_key)
        return api_key

    def create_widgets(self):
        self.style = ttk.Style()
        self.frame = ttk.Frame(self.master, padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(self.frame, text="Topic:").grid(column=0, row=0, sticky=tk.W)
        self.topic_entry = ttk.Entry(self.frame, width=40)
        self.topic_entry.grid(column=1, row=0, sticky=(tk.W, tk.E))

        ttk.Label(self.frame, text="Days ago:").grid(column=0, row=1, sticky=tk.W)
        self.days_entry = ttk.Entry(self.frame, width=10)
        self.days_entry.grid(column=1, row=1, sticky=(tk.W, tk.E))
        self.days_entry.insert(0, "30")  # Default value

        ttk.Label(self.frame, text="Max Results:").grid(column=0, row=2, sticky=tk.W)
        self.results_entry = ttk.Entry(self.frame, width=10)
        self.results_entry.grid(column=1, row=2, sticky=(tk.W, tk.E))
        self.results_entry.insert(0, "10")  # Default value

        self.search_button = ttk.Button(self.frame, text="Search", command=self.start_search)
        self.search_button.grid(column=1, row=3, sticky=tk.E)

        self.clear_button = ttk.Button(self.frame, text="Clear Screen", command=self.clear_screen)
        self.clear_button.grid(column=0, row=3, sticky=tk.W)

        self.trending_button = ttk.Button(self.frame, text="Get Trending", command=self.start_trending_search)
        self.trending_button.grid(column=1, row=4, sticky=tk.E)

        self.results = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD, width=80, height=20)
        self.results.grid(column=0, row=5, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.progress_bar = ttk.Progressbar(self.frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.progress_bar.grid(column=0, row=6, columnspan=2, sticky=(tk.W, tk.E))

        self.status_label = ttk.Label(self.frame, text="")
        self.status_label.grid(column=0, row=7, columnspan=2, sticky=(tk.W, tk.E))

        self.use_api_checkbox = ttk.Checkbutton(self.frame, text="Use API Key",
                                                variable=self.use_api_var,
                                                command=self.toggle_api_use)
        self.use_api_checkbox.grid(column=0, row=8, sticky=tk.W)

        self.save_button = ttk.Button(self.frame, text="Save Results", command=self.save_results)
        self.save_button.grid(column=1, row=8, sticky=tk.W)

        self.change_api_button = ttk.Button(self.frame, text="Change API Key", command=self.change_api_key)
        self.change_api_button.grid(column=1, row=8, sticky=tk.E)

        self.dark_mode_button = ttk.Button(self.frame, text="Toggle Dark Mode", command=self.toggle_dark_mode)
        self.dark_mode_button.grid(column=1, row=9, sticky=tk.E)

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(5, weight=1)

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

    def toggle_dark_mode(self):
        if self.dark_mode:
            self.style.theme_use('default')
            self.results.config(bg='white', fg='black')
        else:
            self.style.theme_use('clam')
            self.style.configure('TFrame', background='#333333')
            self.style.configure('TLabel', background='#333333', foreground='white')
            self.style.configure('TButton', background='#333333', foreground='white')
            self.style.configure('TEntry', fieldbackground='#555555', foreground='white')
            self.style.configure('TCheckbutton', background='#333333', foreground='white')
            self.style.configure('TProgressbar', background='#333333', foreground='white')
            self.results.config(bg='#333333', fg='white')

        self.dark_mode = not self.dark_mode

    def start_search(self):
        threading.Thread(target=self.search_videos, daemon=True).start()

    def start_trending_search(self):
        threading.Thread(target=self.search_trending_videos, daemon=True).start()

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
                videos = self.scrape_youtube_search(topic, max_results, days_ago)

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

    def search_trending_videos(self):
        max_results = int(self.results_entry.get())

        self.results.delete('1.0', tk.END)
        self.progress_bar['value'] = 0
        self.status_label.config(text="Searching trending videos...")
        self.master.update()

        try:
            if self.api_key:
                videos = self.get_trending_videos_api(max_results)
                if not videos:
                    self.status_label.config(text="No trending videos found")
                    return

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

    def get_trending_videos_api(self, max_results):
        trending_response = self.youtube.videos().list(
            part='snippet',
            chart='mostPopular',
            regionCode='US',
            maxResults=max_results
        ).execute()

        videos = []
        for item in trending_response['items']:
            video = {
                'name': item['snippet']['title'],
                'date': item['snippet']['publishedAt'],
                'video_id': item['id']
            }
            videos.append(video)
        return videos

    def scrape_youtube_search(self, query, max_results=10, days_ago=30):
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

                if (datetime.now() - self.parse_date(publish_date)).days <= days_ago:
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
            date = current_date - timedelta(days=months*30)  # Approximate
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
            response = self.youtube.videos().list(
                part='statistics',
                id=video_id
            ).execute()

            stats = response['items'][0]['statistics']
            views = stats.get('viewCount', 'N/A')
            likes = stats.get('likeCount', 'N/A')
            comments = stats.get('commentCount', 'N/A')
        except Exception as e:
            views, likes, comments = 'N/A', 'N/A', 'N/A'
            print(f"Error fetching analytics: {e}")

        return {
            'views': views,
            'likes': likes,
            'comments': comments
        }

    def get_video_info_scrape(self, video_id):
        url = f"https://www.youtube.com/watch?v={video_id}"
        response = requests.get(url)
        script = re.search(r"var ytInitialData = ({.*?});", response.text).group(1)
        data = json.loads(script)
        video_data = data['contents']['twoColumnWatchNextResults']['results']['results']['contents'][0]['videoPrimaryInfoRenderer']

        title = video_data['title']['runs'][0]['text']
        views = 'N/A'

        try:
            views = video_data['viewCount']['videoViewCountRenderer']['viewCount']['simpleText']
        except KeyError:
            pass

        return {'title': title, 'views': views}

    def view_specific_video(self, video_id):
        webbrowser.open(f"https://www.youtube.com/watch?v={video_id}")

    def clear_screen(self):
        self.results.delete('1.0', tk.END)

    def save_results(self):
        content = self.results.get('1.0', tk.END)
        if content.strip() == "":
            messagebox.showinfo("Info", "No results to save")
            return

        file_types = [
            ("CSV files", "*.csv"),
            ("All files", "*.*")
        ]
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=file_types)
        if not file_path:
            return

        with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['Name', 'Date', 'Video ID', 'Views', 'Likes', 'Comments'])
            for i in range(int(self.results.index('end-1c').split('.')[0])):
                line = self.results.get(f"{i + 1}.0", f"{i + 1}.end").strip()
                if line.startswith("Name:"):
                    name = line[len("Name: "):]
                elif line.startswith("Date:"):
                    date = line[len("Date: "):]
                elif line.startswith("Video ID:"):
                    video_id = line[len("Video ID: "):]
                elif line.startswith("Views:"):
                    views = line[len("Views: "):]
                elif line.startswith("Likes:"):
                    likes = line[len("Likes: "):]
                elif line.startswith("Comments:"):
                    comments = line[len("Comments: "):]
                    writer.writerow([name, date, video_id, views, likes, comments])

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeScraperApp(root)
    root.mainloop()
