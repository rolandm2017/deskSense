
def join_video_name(base_name, middle, ending):
    return base_name + middle + ending


def get_loop_index_from_video(video_name):
    split_up = video_name.split("_")
    iteration = int(split_up[1].split(".")[0])
    return iteration


def name_new_vid(base_name, index, ending):
    return base_name + str(index) + ending


def get_filtered_vid_name(s):
    name, extension = s.split(".")
    return name + "-filtered" + "." + extension


def get_compressed_name_for_vid(s):
    name, extension = s.split(".")
    return name + "_sml" + "." + extension
