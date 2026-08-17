import tempfile
import unittest

import brightdata
import schema


class FakeTokenizer:
    def encode(self, text, add_special_tokens=True, truncation=True, max_length=128):
        pieces = [100 + len(part) for part in text.split()]
        if truncation:
            pieces = pieces[: max(0, max_length - 2)]
        return [101] + pieces + [102] if add_special_tokens else pieces


class BrightDataAdapterSuite(unittest.TestCase):
    def test_row_to_tsv_maps_core_fields(self):
        row = {
            "id": "tweet-1",
            "user_posted": "alice",
            "description": "Spark streaming and vector search",
            "date_posted": '"2024-05-29T06:30:33.000Z"',
            "hashtags": '["Spark","VectorSearch"]',
            "followers": "1234",
            "following": "55",
            "is_verified": "true",
            "photos": '["https://example.com/p.jpg"]',
            "videos": "null",
            "quoted_post": "null",
            "parent_post_details": "null",
        }

        tweet_id, tsv = brightdata.row_to_tsv(row, tokenizer=FakeTokenizer())
        cols = tsv.split("\t")

        self.assertEqual(tweet_id, "tweet-1")
        self.assertEqual(len(cols), len(schema.COLUMNS))
        self.assertEqual(cols[2], "tweet-1")
        self.assertEqual(cols[7], "und")
        self.assertEqual(cols[8], "1716964233")
        self.assertEqual(cols[10], "1234")
        self.assertEqual(cols[12], "true")
        self.assertEqual(cols[1], f"Spark{schema.LIST_SEP}VectorSearch")
        self.assertEqual(cols[3], "Photo")

    def test_iter_tsv_rows_respects_offset_and_limit(self):
        csv_text = (
            "id,user_posted,description,date_posted,hashtags,followers,following,"
            "is_verified,photos,videos,quoted_post,parent_post_details\n"
            "1,u1,first post,2024-01-01T00:00:00.000Z,null,1,2,false,null,null,null,null\n"
            "2,u2,second post,2024-01-02T00:00:00.000Z,null,3,4,false,null,null,null,null\n"
            "3,u3,third post,2024-01-03T00:00:00.000Z,null,5,6,false,null,null,null,null\n"
        )
        with tempfile.NamedTemporaryFile("w+", encoding="utf-8", suffix=".csv") as fh:
            fh.write(csv_text)
            fh.flush()

            rows = list(
                brightdata.iter_tsv_rows(
                    fh.name,
                    limit=1,
                    offset=1,
                    tokenizer=FakeTokenizer(),
                )
            )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "2")

    def test_empty_description_is_skipped(self):
        self.assertIsNone(
            brightdata.row_to_tsv(
                {"id": "empty", "description": " ", "date_posted": "2024-01-01T00:00:00Z"},
                tokenizer=FakeTokenizer(),
            )
        )

    def test_empty_nested_post_metadata_does_not_force_reply_or_quote(self):
        row = {
            "id": "tweet-2",
            "user_posted": "alice",
            "description": "plain top level post",
            "date_posted": "2024-01-01T00:00:00.000Z",
            "hashtags": "null",
            "followers": "1",
            "following": "2",
            "is_verified": "false",
            "photos": "null",
            "videos": "null",
            "quoted_post": '{"description":null,"post_id":null}',
            "parent_post_details": '{"description":null,"post_id":null}',
        }

        _, tsv = brightdata.row_to_tsv(row, tokenizer=FakeTokenizer())
        self.assertEqual(tsv.split("\t")[6], "TopLevel")


if __name__ == "__main__":
    unittest.main()
