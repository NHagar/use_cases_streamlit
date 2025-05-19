import feedparser
import streamlit as st
from openai import OpenAI

# --- Configuration & Helper Functions ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def fetch_feed_items(feed_url, num_items=5):
    """Fetches and parses an RSS feed, returning the specified number of recent items."""
    try:
        feed = feedparser.parse(feed_url)
        return feed.entries[:num_items]
    except Exception as e:
        st.error(f"Error fetching feed from {feed_url}: {e}")
        return []


def mock_llm_process(prompt, item_content):
    """
    Simulates processing by an LLM.
    In a real application, this function would make an API call to an LLM.
    """
    resp = client.responses.create(
        model=st.session_state.selected_llm_model,
        instructions=prompt,
        input=item_content,
    )

    return resp.output_text


# --- Streamlit App UI ---

st.set_page_config(page_title="RSS to LLM Processor", layout="wide")

st.title("RSS Feed to LLM Processor")
st.markdown("""
This app fetches the latest items from your specified RSS feeds,
allows you to define a prompt, and then (simulated) processes each item
with a Large Language Model.
""")

# Initialize session state variables if they don't exist
if "rss_urls_text" not in st.session_state:
    st.session_state.rss_urls_text = """https://rss.arxiv.org/rss/cs.AI/
https://simonwillison.net/atom/everything/
https://news.mit.edu/topic/mitartificial-intelligence2-rss.xml
https://generative-ai-newsroom.com/feed"""
if "fetched_items" not in st.session_state:
    st.session_state.fetched_items = []
if "llm_prompt" not in st.session_state:
    with open("prompt.txt", "r") as f:
        st.session_state.llm_prompt = f.read()
if "llm_outputs" not in st.session_state:
    st.session_state.llm_outputs = []
if "selected_llm_model" not in st.session_state:
    st.session_state.selected_llm_model = (
        "gpt-4o"  # Default model, changed from gpt-4.1-mini
    )

# --- Section 1: RSS Feed Input ---
st.header("1. Add RSS Feed URLs")
st.session_state.rss_urls_text = st.text_area(
    "Enter RSS feed URLs (one per line):",
    value=st.session_state.rss_urls_text,
    height=100,
)

if st.button("Fetch 5 Most Recent Items from Feeds", key="fetch_rss"):
    st.session_state.fetched_items = []  # Clear previous items
    st.session_state.llm_outputs = []  # Clear previous outputs
    urls = [
        url.strip() for url in st.session_state.rss_urls_text.split("\n") if url.strip()
    ]
    if not urls:
        st.warning("Please enter at least one RSS feed URL.")
    else:
        with st.spinner("Fetching RSS items..."):
            all_items = []
            for url in urls:
                st.write(f"Fetching from: {url}")
                items = fetch_feed_items(url, num_items=5)
                if items:
                    all_items.extend(items)
                else:
                    st.error(f"Could not retrieve items from {url}")
            st.session_state.fetched_items = all_items
        if st.session_state.fetched_items:
            st.success(
                f"Successfully fetched {len(st.session_state.fetched_items)} items from the provided feeds."
            )
        else:
            st.error("No items were fetched. Check the URLs and try again.")

# Display fetched items (optional, but good for user feedback)
if st.session_state.fetched_items:
    st.subheader("Fetched RSS Items:")
    for i, item in enumerate(st.session_state.fetched_items):
        item_title = item.get("title", "No Title")
        item_link = item.get("link", "#")
        st.markdown(f"{i + 1}. [{item_title}]({item_link})")
    st.markdown("---")


# --- Section 2: LLM Prompt ---
st.header("2. Define LLM Prompt")

# LLM Model Selector
llm_model_options = ["gpt-4.1", "gpt-4o", "o4-mini"]
st.session_state.selected_llm_model = st.selectbox(
    "Select LLM Model:",
    options=llm_model_options,
    index=llm_model_options.index(
        st.session_state.selected_llm_model
    ),  # Ensure current selection is shown
)

st.session_state.llm_prompt = st.text_area(
    "Edit the LLM prompt below:", value=st.session_state.llm_prompt, height=450
)

# --- Section 3: Process with LLM ---
st.header("3. Process Items with LLM")

if not st.session_state.fetched_items:
    st.info("Fetch some RSS items first before processing with the LLM.")
else:
    if st.button("Process Items with LLM", key="process_llm"):
        if not st.session_state.llm_prompt.strip():
            st.warning("LLM prompt cannot be empty.")
        else:
            st.session_state.llm_outputs = []  # Clear previous outputs
            num_items_to_process = len(st.session_state.fetched_items)
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, item in enumerate(st.session_state.fetched_items):
                item_title = item.get("title", "No Title")
                item_summary = item.get(
                    "summary", item.get("description", "No Summary Available")
                )
                # For simplicity, we'll pass title and summary to the LLM
                content_to_process = f"Title: {item_title}. Summary: {item_summary}"

                status_text.text(
                    f"Processing item {i + 1}/{num_items_to_process}: {item_title[:50]}..."
                )
                llm_output = mock_llm_process(
                    st.session_state.llm_prompt, content_to_process
                )
                st.session_state.llm_outputs.append(
                    {
                        "title": item_title,
                        "link": item.get("link", "#"),
                        "original_content": content_to_process,
                        "llm_output": llm_output,
                    }
                )
                progress_bar.progress((i + 1) / num_items_to_process)

            status_text.success(f"All {num_items_to_process} items processed!")
            progress_bar.empty()  # Clear the progress bar after completion

# --- Section 4: Display LLM Outputs ---
if st.session_state.llm_outputs:
    st.header("4. LLM Outputs")
    for i, output_data in enumerate(st.session_state.llm_outputs):
        with st.expander(f"Output for: {output_data['title']}", expanded=False):
            st.markdown(
                f"**Original Link:** [{output_data['title']}]({output_data['link']})"
            )
            # st.markdown(f"**Content Sent to LLM:**\n```\n{output_data['original_content']}\n```") # Optional: show what was sent
            st.markdown(f"**LLM Output:**\n> {output_data['llm_output']}")
    st.markdown("---")

# --- Footer/Instructions ---
st.sidebar.header("How to Use")
st.sidebar.markdown("""
1.  **Enter RSS URLs:** Add one or more valid RSS feed URLs in the text area under "1. Add RSS Feed URLs". Each URL should be on a new line.
2.  **Fetch Items:** Click the "Fetch 5 Most Recent Items from Feeds" button. The app will retrieve the latest 5 articles from each feed.
3.  **Define Prompt:** Review and edit the LLM prompt in the text area under "2. Define LLM Prompt". This prompt will be used for each RSS item.
4.  **Process with LLM:** Click the "Process Items with LLM" button. The app will simulate sending each fetched item and your prompt to an LLM. A progress bar will show the status.
5.  **View Outputs:** The results from the LLM for each item will be displayed under "4. LLM Outputs". You can expand each item to see its details.
""")
st.sidebar.info("Note: LLM processing is simulated in this demo.")
