class WorkflowBuilder:
    def build_workflow(self, prompt_item, style_preset, seed):
        return {
            "seed": seed,
            "style_preset": style_preset,
            "positive_prompt": prompt_item.positive_prompt,
            "negative_prompt": prompt_item.negative_prompt,
            "sampler": "euler",
            "width": 768,
            "height": 1024,
        }
