- name: Debug with SaaS Debugging
        if: ${{ failure() || steps.build.outcome == 'failure' }}
        uses: ConorJones05/githubactionschatbot@main
        with:
          api_key: testing
          api_url: "https://githubactionschatbot.onrender.com"