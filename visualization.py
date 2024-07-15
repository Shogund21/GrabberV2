import matplotlib.pyplot as plt

def display_trending_chart(videos):
    # Example function to plot a chart of trending videos
    names = [video['name'] for video in videos]
    views = [int(video['views']) for video in videos]

    plt.figure(figsize=(10, 5))
    plt.barh(names, views, color='blue')
    plt.xlabel('Views')
    plt.ylabel('Video Name')
    plt.title('Trending Videos')
    plt.show()
