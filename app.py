import streamlit as st
import pandas as pd
import re
from typing import Tuple, Dict
from trulens.core import Feedback
from trulens.providers.openai import OpenAI as fOpenAI
from trulens.core import TruSession
from trulens.feedback import prompts
import openai

# Initialize the session
#session = TruSession()



# Set OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

