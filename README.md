# LLM-based Advanced AI Search

This project is a demo application designed to practice the LangGraph lifecycle while integrating the Bright Data API for web scraping.

# Overview

The app performs searches across multiple sources, including Google, Bing, and Reddit, based on user queries.
The retrieved results are then analyzed using Large Language Models (LLMs, e.g., GPT-4o) to extract relevant and useful insights.

For Reddit, the application also collects the comments under each post to enrich the analysis.

Finally, the app combines and summarizes the information from all sources (Google, Bing, Reddit) to deliver a concise, meaningful response.

# Limitations

If the scraped data is too large and exceeds the LLM token limit, the model cannot analyze and summarize the content precisely.

This limitation can be addressed using Vector Databases:

After scraping with Bright Data, the data can be stored locally or in the cloud.

When a user submits a query, only the most relevant chunks are retrieved and processed by the LLM, ensuring efficiency and accuracy.
