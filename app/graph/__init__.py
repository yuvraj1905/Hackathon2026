"""
LangGraph orchestration module for the Presales Estimation Engine.

This module replaces the manual pipelining in ProjectPipeline with a
LangGraph StateGraph. The original agent functions are untouched — only
wrapped with thin state adapters that read/write from the shared
PipelineState TypedDict.

Flow:
  START -> domain_detection -> template_expansion -> feature_structuring
        -> estimation -> confidence_calculation -> tech_stack
        -> proposal -> planning -> build_result -> END
"""
