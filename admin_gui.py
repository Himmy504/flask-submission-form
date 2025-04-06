import tkinter as tk
from tkinter import messagebox
import requests

# === CONFIG ===
BACKEND_URL = "https://your-render-url.onrender.com"  # 🔁 Replace this with your actual Render URL
ADMIN_TOKEN = "Allah"
GROUP_NAME = "IslamicIQHub"

class AdminApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Admin Panel - IslamicIQHub")
        self.root.geometry("600x400")

        self.posts = []
        self.current_index = 0

        self.title_label = tk.Label(root, text="", font=('Arial', 14, 'bold'))
        self.title_label.pack(pady=10)

        self.content_label = tk.Label(root, text="", wraplength=550, justify="left")
        self.content_label.pack()

        self.votes_label = tk.Label(root, text="", fg="blue")
        self.votes_label.pack(pady=10)

        self.send_button = tk.Button(root, text="✅ Send to Group", command=self.send_to_group)
        self.send_button.pack(pady=5)

        self.next_button = tk.Button(root, text="⏭️ Next Post", command=self.next_post)
        self.next_button.pack()

        self.status_label = tk.Label(root, text="", fg="green")
        self.status_label.pack(pady=5)

        self.load_posts()

    def load_posts(self):
        try:
            response = requests.get(f"{BACKEND_URL}/get_posts")
            if response.status_code == 200:
                all_posts = response.json().get("posts", [])
                # Filter: only show posts that are not posted and have majority allow votes
                self.posts = [
                    post for post in all_posts
                    if not post.get("posted") and post.get("votes", {}).values()
                    and list(post["votes"].values()).count("allow") >= 2
                ]
                if not self.posts:
                    self.status_label.config(text="No approved posts to send.")
                else:
                    self.display_post()
            else:
                messagebox.showerror("Error", "Failed to fetch posts from server.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def display_post(self):
        if self.current_index >= len(self.posts):
            self.status_label.config(text="No more posts.")
            return

        post = self.posts[self.current_index]
        self.title_label.config(text=f"📌 {post.get('title', 'No Title')}")
        self.content_label.config(text=post.get("content", "No content"))
        votes = post.get("votes", {})
        vote_summary = f"Votes: ✅ {list(votes.values()).count('allow')} | ❌ {list(votes.values()).count('deny')}"
        self.votes_label.config(text=vote_summary)

    def send_to_group(self):
        if self.current_index >= len(self.posts):
            return

        post = self.posts[self.current_index]
        post_id = post.get("id")

        try:
            res = requests.post(f"{BACKEND_URL}/send_to_group", data={
                "id": post_id,
                "token": ADMIN_TOKEN,
                "group_name": GROUP_NAME
            })
            if res.status_code == 200:
                self.status_label.config(text="✅ Sent to group successfully!")
                self.current_index += 1
                self.display_post()
            else:
                messagebox.showerror("Error", f"Failed to send post.\n{res.text}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def next_post(self):
        self.current_index += 1
        if self.current_index < len(self.posts):
            self.display_post()
        else:
            self.status_label.config(text="No more posts.")

# === RUN ===
if __name__ == "__main__":
    root = tk.Tk()
    app = AdminApp(root)
    root.mainloop()
