# zcache["session_data"][req.sessionID]["file_ops_blob"][counter] = {
#   "datafile_path": datafile_path,
#   "sa_file_path": path.join(datafile_path, path.basename(filename)),
#   "sadf_type_det": None,
#   "sa_file_path_conv": None,
#   "nodename": ''
# };
import os
import creation
import data_processor
from app import app, sar_modes

SINGLE_MODE = list(enumerate(sar_modes['single'], start=1))
MULTI_MODE = list(enumerate(sar_modes['multiple'], start=1))

def update_cache(sessionID, flag=True, args='A'):
    #FIXME
    params = ','.join(list(sar_modes['single'].keys()))
    if flag:
        arg_data = {
            'argOfsar': args,
            'fields': params
        }
    else:
        arg_data = {
            'argOfsar': 'A',
            'fields': params
        }
    app.cache.hmset("sar_args:%s" % sessionID, arg_data)

def update_file_metadata(sessionID, safile):
    file_metadata = {
          "filename": safile,
          "sadf_type_det": None,
          "sa_file_path_conv": None,
          "nodename": ''
    }
    app.cache.hmset("file_metadata:%s:%s" %
                        (sessionID, safile), file_metadata)

def begin(target, sessionID, form):

    if form.data['check_all']:
        update_cache(sessionID, flag=True, args='A')
    else:
        _tmp = form.data['graph_types']
        update_cache(sessionID, flag=False, args=_tmp)

    try:
        os.makedirs(target)
    except FileExistsError:
        app.logger.info("Folder %s exists.." % target)
    except Exception as E:
        #FIXME check this part and confirm it
        import pdb; pdb.set_trace()
        return 500

    filename_list = []
    for upload in form.datafile:
        filename = upload.filename.rsplit("/")[0]
        update_file_metadata(sessionID, filename)
        filename_list.append(filename)
        destination = os.path.join(target, filename)
        app.logger.info("Accepting incoming file: %s" % filename)
        app.logger.info("Saving it to: %s" % destination)
        upload.save(destination)

    app.cache.set("filenames:%s" % sessionID, filename_list)
    response = {"nodenames_info": []}

    #FIXME: single file upload error: None timestamp (fix for threading.....
    #FIXME: ......wait for file upload, add timeouts to Popen, check close_fds)
    #FIXME: multifile upload not working
    for filename in filename_list:
        nodename, meta, sadf = data_processor.prepare(sessionID,
                                                target, filename)
        result = [filename, sadf, nodename, meta]
        if not nodename:
            #FIXME: on failure, delete all uploaded files
            result.insert(0, False)
        else:
            result.insert(0, True)
        response["nodenames_info"].append(result)

    #FIXME
    return response
