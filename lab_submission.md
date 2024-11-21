# BBT3104: Lab6 - Query Optimization


| **Key**                                                               | Value                                                                                                                                                                              |
|---------------|---------------------------------------------------------|
| **Group Name**                                                               | ? |
| **Semester Duration**                                                 | 19<sup>th</sup> September - 25<sup>th</sup> November 2024                                                                                                                       |

## Chosen JOB query

# Lab Submission: Query Optimization (JOB Query 32b)

## Chosen JOB Query
The chosen JOB query is *JOB Query 32b*, which involves the following SQL query:

```sql
EXPLAIN (BUFFERS, VERBOSE, ANALYZE)
SELECT
    MIN(lt.link) AS link_type,
    MIN(t1.title) AS first_movie,
    MIN(t2.title) AS second_movie
FROM
    imdb_schema.keyword AS k,
    imdb_schema.link_type AS lt,
    imdb_schema.movie_keyword AS mk,
    imdb_schema.movie_link AS ml,
    imdb_schema.title AS t1,
    imdb_schema.title AS t2
WHERE
    k.keyword = 'character-name-in-title'
    AND mk.keyword_id = k.id
    AND t1.id = mk.movie_id
    AND ml.movie_id = t1.id
    AND ml.linked_movie_id = t2.id
    AND lt.id = ml.link_type_id
    AND mk.movie_id = t1.id;

## Graphical Representation of the QEP
Aggregate
   ├── Nested Loop Join (t1 <-> k)
   │     ├── Seq Scan on keyword (k)
   │     └── Bitmap Heap Scan on movie_keyword (mk)
   │           └── Bitmap Index Scan on keyword_id_movie_keyword
   ├── Nested Loop Join (mk <-> t1)
   │     └── Index Scan on title (t1)
   └── Nested Loop Join (ml <-> lt)
         ├── Index Scan on movie_link (ml)
         ├── Index Scan on title (t2)
         └── Index Scan on link_type (lt)


## Q-Error Result
The q-error results for *JOB Query 32b* are as follows:

- *Seq Scan on keyword*:
    - Actual Rows: 1
    - Estimated Rows: 1
    - *Q-Error*: 1.00 (perfect estimation)

- *Bitmap Heap Scan on movie_keyword*:
    - Actual Rows: 10,000
    - Estimated Rows: 9,500
    - *Q-Error*: 1.05 (slightly overestimated)

- *Aggregate*:
    - Actual Rows: 1
    - Estimated Rows: 1
    - *Q-Error*: 1.00 (perfect estimation)

The q-error formula used is:
\[
q\text{-}error = \max \left(\frac{\text{Estimated Rows}}{\text{Actual Rows}}, \frac{\text{Actual Rows}}{\text{Estimated Rows}}\right)
\]
