from .models import Comment

def create_comment(
    request,
    content_type,
    message
):

    return Comment.objects.create(
        user=request.user,
        content_type=content_type,
        message=message
    )

