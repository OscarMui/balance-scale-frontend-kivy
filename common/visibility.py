from kivy.animation import Animation

def show(widget,animation=False):
    if animation:
        anim = Animation(opacity = 1, transition='in_out_cubic', duration=0.5)
        anim.start(widget)
    else:
        widget.opacity = 1

def hide(widget):
    widget.opacity = 0