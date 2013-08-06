import pzx.attachment

def get(request, response):
    id = re.search('\d+', request.get_path()).group(0)
    attachment = pzx.attachment.get(id)
    response.set_header('Content-Length', attachment.size)
    response.set_header('Content-Type', attachment.content_type)
    atta_file = attachment.open_attachment(_attachment)
    for line in atta_file:
        response.write(line)
    atta_file.close()
