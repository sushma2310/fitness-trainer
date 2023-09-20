import av
import os
import sys
import streamlit as st
import cv2
import tempfile
from streamlit_webrtc import VideoHTMLAttributes, webrtc_streamer
from aiortc.contrib.media import MediaRecorder
from utils import get_mediapipe_pose
from process_frame import ProcessFrame
from thresholds import get_thresholds_beginner, get_thresholds_pro
# Your other imports (e.g., processing classes) go here

# Sidebar title and mode selection
st.title('Select Mode')

# Radio button to choose the mode
selected_mode = st.radio('Choose Mode', ['Live Stream', 'Upload Video'])

# Function to process video frames based on the selected mode
def process_video(mode):
    if mode == 'Live Stream':
        # Your live streaming code (similar to live_stream.py)
        # ...
        mode = st.radio('Select Mode', ['Beginner', 'Pro'], horizontal=True)
        thresholds = None 

        if mode == 'Beginner':
            thresholds = get_thresholds_beginner()

        elif mode == 'Pro':
            thresholds = get_thresholds_pro()


        live_process_frame = ProcessFrame(thresholds=thresholds, flip_frame=True)
        # Initialize face mesh solution
        pose = get_mediapipe_pose()


        if 'download' not in st.session_state:
            st.session_state['download'] = False

        output_video_file = f'output_live.flv'

        

        def video_frame_callback(frame: av.VideoFrame):
            frame = frame.to_ndarray(format="rgb24")  # Decode and get RGB frame
            frame, _ = live_process_frame.process(frame, pose)  # Process frame
            return av.VideoFrame.from_ndarray(frame, format="rgb24")  # Encode and return BGR frame


        def out_recorder_factory() -> MediaRecorder:
                return MediaRecorder(output_video_file)


        ctx = webrtc_streamer(
                                key="Squats-pose-analysis",
                                video_frame_callback=video_frame_callback,
                                rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},  # Add this config
                                media_stream_constraints={"video": {"width": {'min':480, 'ideal':480}}, "audio": False},
                                video_html_attrs=VideoHTMLAttributes(autoPlay=True, controls=False, muted=False),
                                out_recorder_factory=out_recorder_factory
                            )


        download_button = st.empty()

        if os.path.exists(output_video_file):
            with open(output_video_file, 'rb') as op_vid:
                download = download_button.download_button('Download Video', data = op_vid, file_name='output_live.flv')

                if download:
                    st.session_state['download'] = True



        if os.path.exists(output_video_file) and st.session_state['download']:
            os.remove(output_video_file)
            st.session_state['download'] = False
            download_button.empty()

    elif mode == 'Upload Video':
        # Your video upload code (similar to upload.py)
        # ...
                
        mode = st.radio('Select Mode', ['Beginner', 'Pro'], horizontal=True)



        thresholds = None 

        if mode == 'Beginner':
            thresholds = get_thresholds_beginner()

        elif mode == 'Pro':
            thresholds = get_thresholds_pro()



        upload_process_frame = ProcessFrame(thresholds=thresholds)

        # Initialize face mesh solution
        pose = get_mediapipe_pose()


        download = None

        if 'download' not in st.session_state:
            st.session_state['download'] = False


        output_video_file = f'output_recorded.mp4'

        if os.path.exists(output_video_file):
            os.remove(output_video_file)


        with st.form('Upload', clear_on_submit=True):
            up_file = st.file_uploader("Upload a Video", ['mp4','mov', 'avi'])
            uploaded = st.form_submit_button("Upload")

        stframe = st.empty()

        ip_vid_str = '<p style="font-family:Helvetica; font-weight: bold; font-size: 16px;">Input Video</p>'
        warning_str = '<p style="font-family:Helvetica; font-weight: bold; color: Red; font-size: 17px;">Please Upload a Video first!!!</p>'

        warn = st.empty()


        download_button = st.empty()

        if up_file and uploaded:
            
            download_button.empty()
            tfile = tempfile.NamedTemporaryFile(delete=False)

            try:
                warn.empty()
                tfile.write(up_file.read())

                vf = cv2.VideoCapture(tfile.name)

                # ---------------------  Write the processed video frame. --------------------
                fps = int(vf.get(cv2.CAP_PROP_FPS))
                width = int(vf.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(vf.get(cv2.CAP_PROP_FRAME_HEIGHT))
                frame_size = (width, height)
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                video_output = cv2.VideoWriter(output_video_file, fourcc, fps, frame_size)
                # -----------------------------------------------------------------------------

                
                txt = st.sidebar.markdown(ip_vid_str, unsafe_allow_html=True)   
                ip_video = st.sidebar.video(tfile.name) 

                while vf.isOpened():
                    ret, frame = vf.read()
                    if not ret:
                        break

                    # convert frame from BGR to RGB before processing it.
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    out_frame, _ = upload_process_frame.process(frame, pose)
                    stframe.image(out_frame)
                    video_output.write(out_frame[...,::-1])

                
                vf.release()
                video_output.release()
                stframe.empty()
                ip_video.empty()
                txt.empty()
                tfile.close()
            
            except AttributeError:
                warn.markdown(warning_str, unsafe_allow_html=True)   



        if os.path.exists(output_video_file):
            with open(output_video_file, 'rb') as op_vid:
                download = download_button.download_button('Download Video', data = op_vid, file_name='output_recorded.mp4')
            
            if download:
                st.session_state['download'] = True



        if os.path.exists(output_video_file) and st.session_state['download']:
            os.remove(output_video_file)
            st.session_state['download'] = False
            download_button.empty()


# Main app title
st.title('AI Fitness Trainer: Exercise Analysis')

# Call the function to process video based on the selected mode
process_video(selected_mode)
