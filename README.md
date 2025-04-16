- name: Debug with SaaS Debugging
        if: ${{ failure() || steps.build.outcome == 'failure' }}
        uses: ConorJones05/githubactionschatbot@main
        with:
          api_key: testing
          api_url: "https://githubactionschatbot.onrender.com"

- name: Debug with SaaS Debugging
        if: ${{ failure() || steps.build.outcome == 'failure' }}
        uses: ConorJones05/githubactionschatbot@main
        with:
          api_key: test_api_key_12345abcdef67890ghijklmno


- name: Debug with BuildSage Debugging
if: ${{ failure() || steps.build.outcome == "failure" }}
	uses: ConorJones05/githubactionschatbot@main
	with:
		api_key: test