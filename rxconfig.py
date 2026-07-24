import reflex as rx

config = rx.Config(
    app_name="exchange",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(
                radius="full",
                has_background=True,
                accent_color="cyan",
                scaling="90%",
            )
        )
    ]
)