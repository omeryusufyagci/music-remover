# Music Remover

This is a simple test I made to see if there were any machine learning models that could accurately detect and remove music from media.

This was possible thanks to `demucs` (https://github.com/facebookresearch/demucs). The results are quite impressive in terms of audio quality. However, it's quite slow and only really suitable for offline analysis of relatively small sized media. 

I'm looking into using a lighter model (demucs can detect upto musical instruments which are not needed for this purpose) that I can implement in C++, to hopefully achieve something that could be used in realtime with some initial delay. 

## Usage

After installing the dependencies run the app.py, and open the locally hosted frontend on your browser. 

You'll be prompted for a youtube video URL, provide the link and click process.

You can examine the stages from the console and the video will be available for playback on the frontend, once the processing is finished.

## License

This test is released under MIT license as it uses Demucs, which can be found in the [LICENSE](LICENSE) file.
