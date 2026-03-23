import taichi as ti
import math

ti.init(arch=ti.gpu)

# -----------------------------
# 基本参数
# -----------------------------
WIDTH = 700
HEIGHT = 700

eye_pos = ti.Vector([0.0, 0.0, 5.0])

# 三角形三个顶点（齐次坐标）
vertices = [
    ti.Vector([ 2.0, 0.0, -2.0, 1.0]),
    ti.Vector([ 0.0, 2.0, -2.0, 1.0]),
    ti.Vector([-2.0, 0.0, -2.0, 1.0]),
]

edges = [(0, 1), (1, 2), (2, 0)]


# -----------------------------
# Model 矩阵：绕 Z 轴旋转
# -----------------------------
def get_model_matrix(angle):
    rad = angle * math.pi / 180.0
    c = math.cos(rad)
    s = math.sin(rad)

    model = ti.Matrix([
        [ c, -s, 0.0, 0.0],
        [ s,  c, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ])
    return model


# -----------------------------
# View 矩阵：把相机平移到原点
# -----------------------------
def get_view_matrix(eye_pos):
    view = ti.Matrix([
        [1.0, 0.0, 0.0, -eye_pos[0]],
        [0.0, 1.0, 0.0, -eye_pos[1]],
        [0.0, 0.0, 1.0, -eye_pos[2]],
        [0.0, 0.0, 0.0, 1.0],
    ])
    return view


# -----------------------------
# Projection 矩阵：透视投影
# -----------------------------
def get_projection_matrix(eye_fov, aspect_ratio, zNear, zFar):
    fov_rad = eye_fov * math.pi / 180.0

    # 注意：相机看向 -Z
    n = -zNear
    f = -zFar

    t = math.tan(fov_rad / 2.0) * abs(n)
    b = -t
    r = aspect_ratio * t
    l = -r

    # 透视 -> 正交
    persp_to_ortho = ti.Matrix([
        [n,   0.0,   0.0,    0.0],
        [0.0, n,     0.0,    0.0],
        [0.0, 0.0, n + f, -n * f],
        [0.0, 0.0,   1.0,    0.0],
    ])

    # 正交投影 = 缩放 * 平移
    ortho_translate = ti.Matrix([
        [1.0, 0.0, 0.0, -(r + l) / 2.0],
        [0.0, 1.0, 0.0, -(t + b) / 2.0],
        [0.0, 0.0, 1.0, -(n + f) / 2.0],
        [0.0, 0.0, 0.0, 1.0],
    ])

    ortho_scale = ti.Matrix([
        [2.0 / (r - l), 0.0, 0.0, 0.0],
        [0.0, 2.0 / (t - b), 0.0, 0.0],
        [0.0, 0.0, 2.0 / (n - f), 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ])

    ortho = ortho_scale @ ortho_translate
    projection = ortho @ persp_to_ortho
    return projection


# -----------------------------
# 顶点变换：MVP + 透视除法 + 屏幕映射
# -----------------------------
def transform_vertex(v, mvp):
    clip = mvp @ v

    # 透视除法
    ndc = ti.Vector([
        clip[0] / clip[3],
        clip[1] / clip[3],
        clip[2] / clip[3],
    ])

    # 映射到 GUI 的 [0,1] 坐标
    screen = ti.Vector([
        (ndc[0] + 1.0) * 0.5,
        (ndc[1] + 1.0) * 0.5,
    ])
    return screen


# -----------------------------
# 主程序
# -----------------------------
def run():
    gui = ti.GUI("Experiment 2 - MVP Triangle", res=(WIDTH, HEIGHT))
    angle = 0.0

    while gui.running:
        for e in gui.get_events(ti.GUI.PRESS):
            if e.key == ti.GUI.ESCAPE:
                gui.running = False
            elif e.key == 'a':
                angle += 10.0
            elif e.key == 'd':
                angle -= 10.0

        model = get_model_matrix(angle)
        view = get_view_matrix(eye_pos)
        projection = get_projection_matrix(
            eye_fov=45.0,
            aspect_ratio=1.0,
            zNear=0.1,
            zFar=50.0
        )

        # 题目要求顺序：MVP = P @ V @ M
        mvp = projection @ view @ model

        screen_vertices = [transform_vertex(v, mvp) for v in vertices]

        gui.clear(0x000000)

            # 三条边分别设置不同颜色
        edge_colors = [
            0xFF0000,  # 红
            0x00FF00,  # 绿
            0x0000FF,  # 蓝
        ]

        for k, (i, j) in enumerate(edges):
            p0 = (screen_vertices[i][0], screen_vertices[i][1])
            p1 = (screen_vertices[j][0], screen_vertices[j][1])
            gui.line(begin=p0, end=p1, radius=2, color=edge_colors[k])


        gui.show()


if __name__ == "__main__":
    run()
