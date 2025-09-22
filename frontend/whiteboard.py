import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8002")

def get_auth_headers():
    """Get authentication headers from session state"""
    if "access_token" in st.session_state:
        return {"Authorization": f"Bearer {st.session_state.access_token}"}
    return {}

def get_current_organization():
    """Get the currently selected organization from session state"""
    return st.session_state.get("selected_barn_id")

def create_post_form():
    """Display form to create a new message board post"""
    st.subheader("📝 Create New Post")

    # Photo upload functionality outside the form
    st.markdown("**📸 Optional: Add a photo to your post**")

    # Add custom CSS to style the file uploader
    st.markdown("""
    <style>
    /* Target the file uploader container */
    [data-testid="stFileUploader"] {
        background-color: white !important;
    }

    /* Target the drag and drop area */
    [data-testid="stFileUploader"] > div > div > div {
        background-color: white !important;
        background: white !important;
        border: 2px dashed #1f77b4 !important;
    }

    /* Target the inner content */
    [data-testid="stFileUploader"] section {
        background-color: white !important;
        background: white !important;
    }

    /* Remove blue background from file uploader */
    .stFileUploader section {
        background-color: white !important;
        background: white !important;
    }

    .stFileUploader section div {
        background-color: white !important;
        background: white !important;
    }

    /* Hide the Browse files button inside the drag area */
    [data-testid="stFileUploader"] button {
        display: none !important;
    }

    /* Hide the button text in the file uploader */
    [data-testid="stFileUploader"] section button {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Create two columns for the buttons
    col_browse, col_camera = st.columns(2)

    uploaded_file = None
    camera_photo = None

    with col_browse:
        st.markdown("**📁 Browse Files**")
        uploaded_file = st.file_uploader(
            "",  # Remove the label since we have it above
            type=['png', 'jpg', 'jpeg', 'webp'],
            help="Upload a photo to include with your post",
            key="whiteboard_file_upload",
            label_visibility="collapsed"
        )

    with col_camera:
        st.markdown("**📷 Camera**")
        # Camera toggle button
        if 'whiteboard_camera_enabled' not in st.session_state:
            st.session_state.whiteboard_camera_enabled = False

        if st.button("📷 Enable Camera" if not st.session_state.whiteboard_camera_enabled else "📷 Disable Camera",
                    type="secondary", key="camera_toggle"):
            st.session_state.whiteboard_camera_enabled = not st.session_state.whiteboard_camera_enabled
            st.rerun()

        if st.session_state.whiteboard_camera_enabled:
            camera_photo = st.camera_input("Take a photo", help="Take a photo directly with your camera", key="whiteboard_camera")

    # Use either uploaded file or camera photo
    photo_to_upload = uploaded_file if uploaded_file else camera_photo

    if photo_to_upload:
        st.image(photo_to_upload, caption="Photo to include with post", width=300)

    with st.form("create_post_form"):
        col1, col2 = st.columns([2, 1])

        with col1:
            title = st.text_input(
                "Title *",
                placeholder="What's on your mind?",
                help="Brief title for your post"
            )

        with col2:
            category = st.selectbox(
                "Category",
                options=[
                    "general", "announcement", "maintenance",
                    "health_alert", "training", "supplies",
                    "weather", "emergency", "other"
                ],
                format_func=lambda x: x.replace("_", " ").title()
            )

        content = st.text_area(
            "Content *",
            placeholder="Share your message with the barn...",
            height=120,
            help="Main content of your post"
        )

        tags = st.text_input(
            "Tags (optional)",
            placeholder="horse names, equipment, etc. (comma-separated)",
            help="Add tags to help others find your post"
        )

        # Pin option
        is_pinned = st.checkbox(
            "📌 Pin this post",
            help="Pinned posts appear at the top of the message board"
        )

        submitted = st.form_submit_button("📤 Post Message", use_container_width=True)

    # Buttons outside the form
    col_cancel = st.columns(1)[0]
    with col_cancel:
        if st.button("❌ Cancel", use_container_width=True, help="Cancel and return to posts"):
            # Set flag to return to posts view
            st.session_state["show_posts_after_create"] = True
            st.rerun()

    if submitted:
        if not title.strip() or not content.strip():
            st.error("Title and content are required")
            return

        if hasattr(st.session_state, 'selected_barn_id') and st.session_state.selected_barn_id:
            organization_id = st.session_state.selected_barn_id
        else:
            st.error("Please select a barn first")
            return

        try:
            # Choose endpoint based on whether we have an image
            if photo_to_upload:
                # Use multipart form endpoint with image
                files = {
                    "image": (photo_to_upload.name, photo_to_upload.getvalue(), photo_to_upload.type)
                }
                data = {
                    "title": title.strip(),
                    "content": content.strip(),
                    "category": category,
                    "tags": tags.strip() if tags.strip() else "",
                    "is_pinned": is_pinned
                }

                response = requests.post(
                    f"{API_BASE_URL}/api/v1/whiteboard/posts/with-image",
                    files=files,
                    data=data,
                    headers=get_auth_headers(),
                    params={"organization_id": organization_id}
                )
            else:
                # Use regular JSON endpoint
                post_data = {
                    "title": title.strip(),
                    "content": content.strip(),
                    "category": category,
                    "tags": tags.strip() if tags.strip() else None,
                    "is_pinned": is_pinned
                }

                response = requests.post(
                    f"{API_BASE_URL}/api/v1/whiteboard/posts",
                    json=post_data,
                    headers=get_auth_headers(),
                    params={"organization_id": organization_id}
                )

            if response.status_code == 201:
                # Set flag to show only posts view on next reload
                st.session_state["show_posts_after_create"] = True
                st.rerun()
            else:
                st.error(f"Failed to create post: {response.text}")

        except Exception as e:
            st.error(f"Error creating post: {str(e)}")

def display_post_card(post: Dict):
    """Display a single post card"""
    with st.container():
        # Post header
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            # Title with category badge
            category_emoji = {
                "general": "💬", "announcement": "📢", "maintenance": "🔧",
                "health_alert": "🚨", "training": "🏇", "supplies": "📦",
                "weather": "🌤️", "emergency": "🆘", "other": "📝"
            }
            emoji = category_emoji.get(post.get("category", "general"), "📝")

            title = post.get("title", "Untitled")
            if post.get("is_pinned"):
                title = f"📌 {title}"

            st.markdown(f"### {emoji} {title}")

        with col2:
            # Category badge
            category = post.get("category", "general").replace("_", " ").title()
            st.markdown(f"<span style='background-color: #f0f2f6; padding: 2px 8px; border-radius: 12px; font-size: 0.8em'>{category}</span>",
                       unsafe_allow_html=True)

        with col3:
            # Creation date
            created_at = post.get("created_at")
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    st.caption(f"📅 {dt.strftime('%m/%d %H:%M')}")
                except:
                    st.caption("📅 Recently")

        # Post content
        st.markdown(post.get("content", ""))

        # Tags
        tags = post.get("tags", [])
        if tags:
            tag_str = " ".join([f"`{tag.strip()}`" for tag in tags if tag.strip()])
            if tag_str:
                st.markdown(f"🏷️ {tag_str}")

        # Display thumbnail if image is available
        attachment_count = post.get("attachment_count", 0)
        if attachment_count > 0:
            try:
                # Get organization_id from current session
                organization_id = get_current_organization()
                if organization_id:
                    # Fetch post details to get attachment info
                    response = requests.get(
                        f"{API_BASE_URL}/api/v1/whiteboard/posts/{post['id']}",
                        headers=get_auth_headers(),
                        params={"organization_id": organization_id}
                    )

                    if response.status_code == 200:
                        post_details = response.json()
                        attachments = post_details.get("attachments", [])

                        # Find the first image attachment
                        image_attachment = None
                        for attachment in attachments:
                            if attachment.get("attachment_type") == "image":
                                image_attachment = attachment
                                break

                        if image_attachment:
                            # Fetch and display thumbnail image
                            image_url = f"{API_BASE_URL}/api/v1/whiteboard/images/{image_attachment['id']}"
                            img_response = requests.get(
                                image_url,
                                headers=get_auth_headers(),
                                params={"organization_id": organization_id}
                            )

                            if img_response.status_code == 200:
                                st.image(
                                    img_response.content,
                                    caption=f"📷 {image_attachment.get('original_filename', 'Image')}",
                                    width=150
                                )
                            else:
                                st.markdown("📎 *Image attachment (click 'View Details' to see)*")
                        else:
                            st.markdown("📎 *File attachments (click 'View Details' to see)*")
                    else:
                        st.markdown("📎 *Attachments (click 'View Details' to see)*")
                else:
                    st.markdown("📎 *Attachments (click 'View Details' to see)*")

            except Exception as e:
                # Fallback to simple indicator if thumbnail loading fails
                st.markdown("📎 *Attachments (click 'View Details' to see)*")

        # Post metadata and actions
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            author = post.get("author_name", "Unknown")
            st.caption(f"👤 {author}")

        with col2:
            comment_count = post.get("comment_count", 0)
            st.caption(f"💬 {comment_count} comment{'s' if comment_count != 1 else ''}")

        with col3:
            if st.button("💬 View Details", key=f"view_post_{post['id']}", help="View post details and comments"):
                st.session_state[f"show_post_details_{post['id']}"] = True
                st.rerun()

        with col4:
            # Show delete button only for post author
            current_user_email = st.session_state.get("user", {}).get("email")
            post_author_email = post.get("author_email")
            if current_user_email and post_author_email and current_user_email == post_author_email:
                if st.button("🗑️ Delete", key=f"delete_post_{post['id']}", help="Delete this post"):
                    delete_post(post['id'])

        st.divider()

def delete_post(post_id: int):
    """Delete a message board post"""
    if hasattr(st.session_state, 'selected_barn_id') and st.session_state.selected_barn_id:
        organization_id = st.session_state.selected_barn_id
    else:
        st.error("Please select a barn first")
        return

    try:
        response = requests.delete(
            f"{API_BASE_URL}/api/v1/whiteboard/posts/{post_id}",
            headers=get_auth_headers(),
            params={"organization_id": organization_id}
        )

        if response.status_code == 204:
            st.success("✅ Post deleted successfully!")
            st.rerun()
        else:
            st.error(f"Failed to delete post: {response.text}")

    except Exception as e:
        st.error(f"Error deleting post: {str(e)}")

def display_post_details(post_id: int):
    """Display detailed view of a post with comments"""
    if hasattr(st.session_state, 'selected_barn_id') and st.session_state.selected_barn_id:
        organization_id = st.session_state.selected_barn_id
    else:
        st.error("Please select a barn first")
        return

    try:
        # Get post details
        response = requests.get(
            f"{API_BASE_URL}/api/v1/whiteboard/posts/{post_id}",
            headers=get_auth_headers(),
            params={"organization_id": organization_id}
        )

        if response.status_code != 200:
            st.error("Failed to load post details")
            return

        post = response.json()

        # Display post
        st.subheader(f"📄 {post.get('title', 'Untitled')}")

        # Post metadata
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            category = post.get("category", "general").replace("_", " ").title()
            st.metric("Category", category)

        with col2:
            st.metric("Author", post.get("author_name", "Unknown"))

        with col3:
            created_at = post.get("created_at")
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    st.metric("Posted", dt.strftime('%m/%d/%Y %H:%M'))
                except:
                    st.metric("Posted", "Recently")

        with col4:
            comment_count = len(post.get("comments", []))
            st.metric("Comments", comment_count)

        # Post content
        st.markdown("### Content")
        st.markdown(post.get("content", ""))

        # Tags
        tags = post.get("tags", [])
        if tags:
            st.markdown("### Tags")
            tag_str = " ".join([f"`{tag.strip()}`" for tag in tags if tag.strip()])
            if tag_str:
                st.markdown(f"🏷️ {tag_str}")

        # Display attachments/images
        attachments = post.get("attachments", [])
        if attachments:
            st.markdown("### 📸 Images")
            for attachment in attachments:
                if attachment.get("attachment_type") == "image":
                    try:
                        # Fetch image data with authentication headers
                        image_url = f"{API_BASE_URL}/api/v1/whiteboard/images/{attachment['id']}"
                        response = requests.get(
                            image_url,
                            headers=get_auth_headers(),
                            params={"organization_id": organization_id}
                        )

                        if response.status_code == 200:
                            # Display the image using the binary data
                            st.image(
                                response.content,
                                caption=f"📷 {attachment.get('original_filename', 'Image')}",
                                width=400
                            )
                        else:
                            st.error(f"Could not load image: {attachment.get('original_filename', 'Unknown')} (Status: {response.status_code})")
                    except Exception as e:
                        st.error(f"Error loading image: {attachment.get('original_filename', 'Unknown')} - {str(e)}")

        # Comments section
        st.markdown("### 💬 Comments")

        comments = post.get("comments", [])
        if comments:
            for comment in comments:
                with st.container():
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"**{comment.get('author_name', 'Unknown')}**")
                        st.markdown(comment.get("content", ""))

                    with col2:
                        created_at = comment.get("created_at")
                        if created_at:
                            try:
                                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                st.caption(dt.strftime('%m/%d %H:%M'))
                            except:
                                st.caption("Recently")

                    st.divider()
        else:
            st.info("No comments yet. Be the first to comment!")

        # Add comment form
        st.markdown("### ✍️ Add Comment")
        with st.form(f"add_comment_{post_id}"):
            comment_content = st.text_area(
                "Your comment:",
                placeholder="Share your thoughts...",
                height=100
            )

            col1, col2 = st.columns([1, 4])
            with col1:
                submit_comment = st.form_submit_button("💬 Comment")

            if submit_comment and comment_content.strip():
                try:
                    comment_data = {
                        "content": comment_content.strip(),
                        "post_id": post_id
                    }

                    response = requests.post(
                        f"{API_BASE_URL}/api/v1/whiteboard/posts/{post_id}/comments",
                        json=comment_data,
                        headers=get_auth_headers(),
                        params={"organization_id": organization_id}
                    )

                    if response.status_code == 201:
                        st.success("✅ Comment added!")
                        st.rerun()
                    else:
                        st.error(f"Failed to add comment: {response.text}")

                except Exception as e:
                    st.error(f"Error adding comment: {str(e)}")

        # Back button
        if st.button("⬅️ Back to Message Board"):
            if f"show_post_details_{post_id}" in st.session_state:
                del st.session_state[f"show_post_details_{post_id}"]
            st.rerun()

    except Exception as e:
        st.error(f"Error loading post details: {str(e)}")

def show_posts_content(organization_id: str):
    """Display posts content (extracted for reuse)"""
    # Filters and search
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_term = st.text_input(
            "🔍 Search posts",
            placeholder="Search titles and content...",
            help="Search in post titles and content"
        )

    with col2:
        category_filter = st.selectbox(
            "Filter by category",
            options=["all"] + [
                "general", "announcement", "maintenance",
                "health_alert", "training", "supplies",
                "weather", "emergency", "other"
            ],
            format_func=lambda x: "All Categories" if x == "all" else x.replace("_", " ").title()
        )

    with col3:
        show_pinned = st.checkbox("📌 Pinned only", help="Show only pinned posts")

    # Load posts
    try:
        params = {
            "organization_id": organization_id,
            "page": 1,
            "page_size": 50
        }

        if search_term:
            params["search"] = search_term

        if category_filter != "all":
            params["category"] = category_filter

        if show_pinned:
            params["pinned_only"] = True

        response = requests.get(
            f"{API_BASE_URL}/api/v1/whiteboard/posts",
            headers=get_auth_headers(),
            params=params
        )

        if response.status_code == 200:
            data = response.json()
            posts = data.get("posts", [])

            if posts:
                st.info(f"📄 Showing {len(posts)} of {data.get('total', 0)} posts")

                for post in posts:
                    display_post_card(post)
            else:
                if search_term or category_filter != "all" or show_pinned:
                    st.info("🔍 No posts found matching your filters. Try adjusting your search criteria.")
                else:
                    st.info("📝 No posts yet. Be the first to share something with your barn!")

        else:
            st.error("Failed to load posts")

    except Exception as e:
        st.error(f"Error loading message board: {str(e)}")

def show_whiteboard_page():
    """Main message board page"""
    st.title("📋 Barn Message Board")

    # Check authentication
    if "access_token" not in st.session_state:
        st.error("Please log in to access the message board")
        return

    # Check organization selection - fix the logic to match main app
    if hasattr(st.session_state, 'selected_barn_id') and st.session_state.selected_barn_id:
        organization_id = st.session_state.selected_barn_id
    else:
        st.error("Please select a barn from the sidebar")
        return

    # Check if we should show post details
    for key in st.session_state.keys():
        if key.startswith("show_post_details_"):
            post_id = int(key.split("_")[-1])
            display_post_details(post_id)
            return

    # Check if we should show posts view after successful creation
    if st.session_state.get("show_posts_after_create", False):
        # Clear the flag
        del st.session_state["show_posts_after_create"]
        # Show posts only view with success message
        st.success("✅ Post created successfully!")
        st.subheader("📋 Posts")
        # Show the posts content directly (same as tab1 content)
        show_posts_content(organization_id)
        return

    # Main message board interface using tabs
    tab1, tab2 = st.tabs(["📋 Posts", "✏️ Create Post"])

    with tab1:
        show_posts_content(organization_id)

    with tab2:
        create_post_form()

# Main execution
if __name__ == "__main__":
    show_whiteboard_page()
else:
    show_whiteboard_page()