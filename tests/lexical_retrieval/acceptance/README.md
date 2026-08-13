# Live multimodal lexical acceptance

This opt-in journey uses NASA's public `GPM: Meet the Team: Dave McComas`
asset as one coherent image, audio, video, and authored-subtitle authority. The
downloaded and derived files live in ignored `.assets/`; production code sees
only ordinary bytes through PostgreSQL binary Storage and exact Resolvers.

The preparation script pins the NASA asset URLs, observed ETags, and SHA-256
digests. It extracts one real frame and the real audio track, then remuxes the
authored WebVTT into Matroska without changing the source streams. NASA's media
usage guidance remains the license and attribution authority:
<https://www.nasa.gov/nasa-brand-center/images-and-media/>.

Run against an explicitly selected disposable, fully migrated PostgreSQL
database and a real Alibaba Model Studio model:

```shell
INKCRE_TEST_DATABASE_URL='...' \
INKCRE_ACCEPTANCE_AI_API_KEY='...' \
INKCRE_ACCEPTANCE_AI_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1' \
INKCRE_ACCEPTANCE_MULTIMODAL_MODEL='qwen3.5-omni-flash' \
pdm run pytest tests/lexical_retrieval/acceptance/test_multimodal_live.py -q
```

The test deliberately does not read project-local credential aliases. CI or a
human operator must opt in with the canonical acceptance environment names.

