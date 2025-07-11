import streamlit as st
#wide page layout
st.set_page_config(layout='wide', page_title="NTU ConfessIt Analysis")
#page theme information is in config.toml file

#necessary import statements
from textblob import TextBlob
import pandas as pd
from wordcloud import WordCloud
from wordcloud import STOPWORDS
import matplotlib.pyplot as plt
import asyncio
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from dotenv import load_dotenv
import os 

#custom stopwords to avoid in the wordcloud
custom_stopwords = {
    "ID", 'Post', 'PM', 'confession', 'confessor', "Others", 
    'Studies', 'Romance', 'Campus', 'Rant', 'Whistleblow',
    'hall', 'friend', 'feeling', 'time', 't', 's', 'NTU', 'ntu', 'Ntu',
    'friends', 'even', 'feel', 'people', 'make', 'want', 'phone', 'one', 'world',
    'hurt', 'something', 'Something', 'Someone', 'someone', 'FRIEND', 'FRIENDS', 'WORLD',
    'HALL', 'ONE', 'PEOPLE', 'FEEL', 'FEELING', "I'm", 'im', 'will', 'WILL', 'can', 'CAN',
    'cca', 'CCA', 'don', 'cos', 'because', "don't", 'now', 'take', 'know', 'm',
    'RS'
    }
all_stopwords = STOPWORDS.union(custom_stopwords)

#categories of confessions for piechart
categories = ['Others', 'Studies', 'Romance',
            'Campus', 'Rant', 'Whistleblow']

#telegram information
load_dotenv()
#use .env file if secrets in streamlit not accessible
api_id = st.secrets["API_ID"] if "API_ID" in st.secrets else os.getenv("API_ID")
api_hash = st.secrets["API_HASH"] if "API_HASH" in st.secrets else os.getenv("API_HASH")
channel_name = st.secrets["CHANNEL_NAME"] if "CHANNEL_NAME" in st.secrets else os.getenv("CHANNEL_NAME")

#function to fetch confessions
async def fetch_messages(limit=30):
    async with TelegramClient("session", api_id, api_hash) as client:
        client.start()
        channel = await client.get_entity(channel_name)
        history = await client(GetHistoryRequest(
            peer= channel, limit= limit,
            offset_date= None, offset_id= 0,
            min_id=0, max_id=0, add_offset=0, hash=0
            #everything 0 since we only want the most recent messages
    ))
    messages = [] #empty list of message objects
    for message in history.messages:
        if message.message:
            messages.append(message.message)
    client.disconnect()
    return messages

def fetch(limits): 
    return asyncio.run(fetch_messages(limits))

#header
#markdown style for custom text
st.markdown("""
    <div style='text-align: center'>
        <h1> 🔐🤫📊 NTU ConfessIt Analysis 📊🤫🔐</h1>
        <h3>Welcome!</h3>
        <h3>See confessions from the community be analysed.</h3>
        <h3>Or enter your own for analysis 🤐.</h3>
    </div>
""", unsafe_allow_html=True)

st.write("Built using Python and Streamlit.")

#making input; default input is telegram
if 'confessions' not in st.session_state:
    st.session_state.confessions = []
selection = st.radio("Select your input method:",
                    ["Fetch from telegram ✉️", "Enter manually ✍️"],
                    index=0, horizontal= True)
if selection == 'Enter manually ✍️':
    #enter multiple confessions
    st.markdown("<h4>Enter confessions one by one: </h4>", unsafe_allow_html=True)
    confessions_input = st.text_area("", height = 200,
                placeholder = "Press enter ⏎ to record one confession.")
    if confessions_input.strip():
        st.session_state.confessions = confessions_input.strip().split('\n')
else:
    #lets user pick how many confessions from tele channel within limits
    st.write("#### Number of confessions must be between 30-100")
    confession_num = st.number_input("How many confessions do you want to fetch?",
                                    min_value=30, max_value=100, step=1)
    if st.button("Fetch confessions"):
        with st.spinner("⏳ Fetching confessions..."):
            st.session_state.confessions = fetch(confession_num)
        st.success(f"✅ Fetched {confession_num} confessions! Click 'Analyse!' for analysis")

#sentiment analysis 
#function to analyse the sentiment 
def analyse_sentiment(confession):
    blob = TextBlob(confession)
    return blob.sentiment.polarity
    #return the polarity for each sentence

#function to classify the sentiment 
def classify_sentiment(polairty_score):
    #we pass the polarity_score returned by the analyse_sentiment function
    if 1.0 >= polairty_score > 0.0:
        return "Positive"
    elif 0.0 > polairty_score >= -1.0:
        return "Negative"
    else:
        return "Neutral"

#function for category analysis
def analyse_category(confession):
    for cat in categories:
        if cat in confession:
            return cat
    return "No category selected"

#click button 
if st.button("Analyse!"):
    with st.spinner("⏳ Analysing..."):
        if not st.session_state.confessions:
            st.write("#### Warning. No confessions for analysis yet.")
        else:
            #looping over each sentence in the confessions to store the data 
            results = [] #final results have each confession's data as a dictionary
            for confession in st.session_state.confessions:
                polarity = analyse_sentiment(confession)
                sentiment = classify_sentiment(polarity)
                category = analyse_category(confession)
                results.append({"Confession":confession, "Polarity":polarity,
                    "Sentiment":sentiment, "Category": category})

            df= pd.DataFrame(results) #makes table
            st.dataframe(df) #shows table

            #built in pie chart with matplotlib
            st.write("### Pie Chart for Confession Category")
            category_count = df['Category'].value_counts()
            fig1, ax1 = plt.subplots()
            ax1.pie(category_count, labels=category_count.index,
                    colors= ['#FFB3BA', '#FFDFBA', '#FFFFBA', 
                            '#BAFFC9', '#BAE1FF', '#FF8B94'],
                    explode= [0.03]*len(category_count.index),
                    autopct='%1.1f', startangle=140)
            ax1.axis('equal')
            st.pyplot(fig1)

            #built in charts with matplotlib
            st.write("### Bar Chart for Negative and Positive Word Use")
            sentiment_counts = df['Sentiment'].value_counts()
            st.bar_chart(sentiment_counts)

            #making columns to arrange wordclouds
            col1, col2 = st.columns(spec=2)
            with col1:
                #word cloud for positive text
                positive = " ".join(df[df['Sentiment'] == 'Positive']['Confession'].tolist())
                if len(positive) == 0:
                    st.write("#### No positive words")
                else:
                    #printing the wordcloud
                    st.write("#### WordCloud for positive words: ")
                    wordcloud = WordCloud(width = 800, height= 800, 
                                background_color= 'white',colormap= 'Paired_r',
                                stopwords= all_stopwords).generate(positive)
                    fig, ax = plt.subplots()
                    ax.imshow(wordcloud, interpolation= 'bilinear')
                    ax.axis('off')
                    st.pyplot(fig)
            with col2:
                #word cloud for negative text
                negative = " ".join(df[df['Sentiment'] == 'Negative']['Confession'].tolist())
                if len(negative) == 0:
                    st.write("#### No negative words")
                else:
                    #printing wordcloud
                    st.write("#### WordCloud for negative words: ")
                    wordcloud = WordCloud(width=800, height=800, 
                                        background_color='white', colormap='Paired_r',
                                        stopwords= all_stopwords).generate(negative)
                    fig, ax = plt.subplots()
                    ax.imshow(wordcloud, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)
            st.success(f"✅ Analysed confessions!")
#end
st.write("Built by Nayantara Rao")