from read4me.parsers.fb2 import parse_fb2_chapters, parse_fb2_cover_artwork


def test_parse_fb2_chapters_extracts_sections_with_titles(tmp_path) -> None:
    fb2_file = tmp_path / "book.fb2"
    fb2_file.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0">
  <body>
    <section>
      <title><p>Chapter 1</p></title>
      <p>First paragraph.</p>
      <p>Second paragraph.</p>
    </section>
    <section>
      <title><p>Chapter 2</p></title>
      <p>Another paragraph.</p>
    </section>
  </body>
</FictionBook>
""",
        encoding="utf-8",
    )

    chapters = parse_fb2_chapters(fb2_file)

    assert [chapter.title for chapter in chapters] == ["Chapter 1", "Chapter 2"]
    assert chapters[0].text == "First paragraph. Second paragraph."
    assert chapters[1].text == "Another paragraph."


def test_parse_fb2_chapters_raises_for_missing_body(tmp_path) -> None:
    fb2_file = tmp_path / "broken.fb2"
    fb2_file.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0"></FictionBook>
""",
        encoding="utf-8",
    )

    try:
        parse_fb2_chapters(fb2_file)
        assert False, "expected ValueError for missing body"
    except ValueError as error:
        assert "body" in str(error).lower()


def test_parse_fb2_cover_artwork_extracts_cover_binary(tmp_path) -> None:
    fb2_file = tmp_path / "book.fb2"
    fb2_file.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0"
             xmlns:l="http://www.w3.org/1999/xlink">
  <description>
    <title-info>
      <coverpage>
        <image l:href="#cover-id"/>
      </coverpage>
    </title-info>
  </description>
  <binary id="cover-id" content-type="image/jpeg">Y292ZXItYnl0ZXM=</binary>
  <body><section><p>x</p></section></body>
</FictionBook>
""",
        encoding="utf-8",
    )

    cover_data, mime_type = parse_fb2_cover_artwork(fb2_file)

    assert cover_data == b"cover-bytes"
    assert mime_type == "image/jpeg"
