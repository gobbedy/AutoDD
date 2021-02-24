from warnings import filterwarnings
# remove annoying warnings from PushshiftAPI
bad_warning1 = "Unable to connect to pushshift.io. Retrying after backoff."
bad_warning2 = "Got non 200 code"
filterwarnings("ignore", message=bad_warning1, module="psaw")
filterwarnings("ignore", message=bad_warning2, module="psaw")