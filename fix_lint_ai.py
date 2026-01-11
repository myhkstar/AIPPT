import os
import re

path = 'backend/services/ai_service.py'
if not os.path.exists(path):
    print(f"File not found: {path}")
    exit(1)

content = open(path, 'r', encoding='utf-8').read()

# 1. Fix blank lines containing whitespace
content = re.sub(r'\n\s+\n', '\n\n', content)

# 2. Fix trailing whitespace
content = re.sub(r'[ \t]+\n', '\n', content)

# 3. Fix specific long lines and indentation
# Line 189: mineru_path docstring
content = content.replace(
    'mineru_path: MinerU URL 路径，格式为\n                /files/mineru/{extract_id}/{rel_path}',
    'mineru_path: MinerU URL 路径，格式为\n                /files/mineru/{extract_id}/{rel_path}'
) # Already fixed in previous turn? Let's check.

# Line 219: logger.debug
content = content.replace(
    'logger.debug(f"Successfully downloaded image: {image.size}, {image.mode}")',
    'logger.debug(\n                f"Successfully downloaded image: {image.size}, {image.mode}"\n            )'
)

# Line 234: docstring
content = content.replace(
    'List of outline items (may contain parts with pages or direct pages)',
    'List of outline items (may contain parts with pages or direct\n            pages)'
)

# Line 264-266: usage logging
content = content.replace(
    'response_time = (time.time() - start_time) * 1000  # Convert to milliseconds\n            provider_name = getattr(self.text_provider, \'provider_type\', \'unknown\')\n            logger.info(f"Text API usage - Provider: {provider_name}, Success: {success}, Response time: {response_time:.2f}ms")',
    'response_time = (time.time() - start_time) * 1000\n            provider_name = getattr(\n                self.text_provider, \'provider_type\', \'unknown\'\n            )\n            logger.info(\n                f"Text API usage - Provider: {provider_name}, "\n                f"Success: {success}, Response time: {response_time:.2f}ms"\n            )'
)

# Line 268: parse_outline_text signature
content = content.replace(
    'def parse_outline_text(self, project_context: ProjectContext) -> List[Dict]:',
    'def parse_outline_text(\n        self, project_context: ProjectContext\n    ) -> List[Dict]:'
)

# Line 271: docstring
content = content.replace(
    'This method analyzes the text and splits it into pages without modifying the original text',
    'This method analyzes the text and splits it into pages without\n        modifying the original text'
)

# Line 310: generate_page_description signature
content = content.replace(
    'def generate_page_description(self, project_context: ProjectContext, outline: List[Dict], \n                                 page_outline: Dict, page_index: int) -> str:',
    'def generate_page_description(\n        self, project_context: ProjectContext, outline: List[Dict],\n        page_outline: Dict, page_index: int\n    ) -> str:'
)

# Line 327: part_info
content = content.replace(
    "part_info = f\"\\nThis page belongs to: {page_outline['part']}\" if 'part' in page_outline else \"\"",
    "part_info = (\n            f\"\\nThis page belongs to: {page_outline['part']}\"\n            if 'part' in page_outline else \"\"\n        )"
)

# Line 352-354: usage logging
content = content.replace(
    'response_time = (time.time() - start_time) * 1000  # Convert to milliseconds\n            provider_name = getattr(self.text_provider, \'provider_type\', \'unknown\')\n            logger.info(f"Text API usage - Provider: {provider_name}, Success: {success}, Response time: {response_time:.2f}ms")',
    'response_time = (time.time() - start_time) * 1000\n            provider_name = getattr(\n                self.text_provider, \'provider_type\', \'unknown\'\n            )\n            logger.info(\n                f"Text API usage - Provider: {provider_name}, "\n                f"Success: {success}, Response time: {response_time:.2f}ms"\n            )'
)

# Line 370: generate_image_prompt signature
content = content.replace(
    'def generate_image_prompt(self, outline: List[Dict], page: Dict, \n                            page_desc: str, page_index: int, \n                            has_material_images: bool = False, \n                            extra_requirements: Optional[str] = None) -> str:',
    'def generate_image_prompt(\n        self, outline: List[Dict], page: Dict,\n        page_desc: str, page_index: int,\n        has_material_images: bool = False,\n        extra_requirements: Optional[str] = None\n    ) -> str:'
)

# Line 413: generate_image signature
content = content.replace(
    'def generate_image(self, prompt: str, ref_image_path: Optional[str] = None, \n                      aspect_ratio: str = \"16:9\", resolution: str = \"2K\",\n                      additional_ref_images: Optional[List[Union[str, Image.Image]]] = None) -> Optional[Image.Image]:',
    'def generate_image(\n        self, prompt: str, ref_image_path: Optional[str] = None,\n        aspect_ratio: str = \"16:9\", resolution: str = \"2K\",\n        additional_ref_images: Optional[List[Union[str, Image.Image]]] = None\n    ) -> Optional[Image.Image]:'
)

# Line 440-441: debug logging
content = content.replace(
    'logger.debug(f\"Additional reference images: {len(additional_ref_images)}\")\n            logger.debug(f\"Config - aspect_ratio: {aspect_ratio}, resolution: {resolution}\")',
    'logger.debug(\n                f\"Additional reference images: {len(additional_ref_images)}\"\n            )\n            logger.debug(\n                f\"Config - aspect_ratio: {aspect_ratio}, \"\n                f\"resolution: {resolution}\"\n            )'
)

# Line 456-458: additional_ref_images processing
content = content.replace(
    'processed_additional_refs.append(Image.open(ref_img))\n                        elif ref_img.startswith(\'http://\') or ref_img.startswith(\'https://\'):\n                            downloaded_img = self.download_image_from_url(ref_img)',
    'processed_additional_refs.append(\n                                Image.open(ref_img)\n                            )\n                        elif (ref_img.startswith(\'http://\') or\n                              ref_img.startswith(\'https://\')):\n                            downloaded_img = (\n                                self.download_image_from_url(ref_img)\n                            )'
)

# Line 460: processed_additional_refs.append
content = content.replace(
    'processed_additional_refs.append(downloaded_img)',
    'processed_additional_refs.append(\n                                    downloaded_img\n                                )'
)

# Line 462-464: mineru path processing
content = content.replace(
    'local_path = self._convert_mineru_path_to_local(ref_img)\n                            if local_path and os.path.exists(local_path):\n                                processed_additional_refs.append(Image.open(local_path))',
    'local_path = (\n                                self._convert_mineru_path_to_local(ref_img)\n                            )\n                            if local_path and os.path.exists(local_path):\n                                processed_additional_refs.append(\n                                    Image.open(local_path)\n                                )'
)

# Line 478: error_detail
content = content.replace(
    'error_detail = f\"Error generating image: {type(e).__name__}: {str(e)}\"',
    'error_detail = (\n                f\"Error generating image: {type(e).__name__}: {str(e)}\"\n            )'
)

# Line 483-485: usage logging
content = content.replace(
    'response_time = (time.time() - start_time) * 1000  # Convert to milliseconds\n            provider_name = getattr(self.image_provider, \'provider_type\', \'unknown\')\n            logger.info(f\"Image API usage - Provider: {provider_name}, Success: {success}, Response time: {response_time:.2f}ms\")',
    'response_time = (time.time() - start_time) * 1000\n            provider_name = getattr(\n                self.image_provider, \'provider_type\', \'unknown\'\n            )\n            logger.info(\n                f\"Image API usage - Provider: {provider_name}, \"\n                f\"Success: {success}, Response time: {response_time:.2f}ms\"\n            )'
)

# Line 490: edit_image signature
content = content.replace(
    'def edit_image(self, prompt: str, current_image_path: str,\n                  aspect_ratio: str = \"16:9\", resolution: str = \"2K\",\n                  original_description: str = None,\n                  additional_ref_images: Optional[List[Union[str, Image.Image]]] = None) -> Optional[Image.Image]:',
    'def edit_image(\n        self, prompt: str, current_image_path: str,\n        aspect_ratio: str = \"16:9\", resolution: str = \"2K\",\n        original_description: str = None,\n        additional_ref_images: Optional[List[Union[str, Image.Image]]] = None\n    ) -> Optional[Image.Image]:'
)

# Line 499: original_description docstring
content = content.replace(
    'original_description: Original page description to include in prompt',
    'original_description: Original page description to include in\n            prompt'
)

# Line 510: FileNotFoundError
content = content.replace(
    'raise FileNotFoundError(f\"Current image not found: {current_image_path}\")',
    'raise FileNotFoundError(\n                    f\"Current image not found: {current_image_path}\"\n                )'
)

# Line 522-524: additional_ref_images processing
content = content.replace(
    'processed_additional_refs.append(Image.open(ref_img))\n                        elif ref_img.startswith(\'http://\') or ref_img.startswith(\'https://\'):\n                            downloaded_img = self.download_image_from_url(ref_img)',
    'processed_additional_refs.append(\n                                Image.open(ref_img)\n                            )\n                        elif (ref_img.startswith(\'http://\') or\n                              ref_img.startswith(\'https://\')):\n                            downloaded_img = (\n                                self.download_image_from_url(ref_img)\n                            )'
)

# Line 526: processed_additional_refs.append
content = content.replace(
    'processed_additional_refs.append(downloaded_img)',
    'processed_additional_refs.append(\n                                    downloaded_img\n                                )'
)

# Line 545: parse_description_to_outline signature
content = content.replace(
    'def parse_description_to_outline(self, project_context: ProjectContext) -> List[Dict]:',
    'def parse_description_to_outline(\n        self, project_context: ProjectContext\n    ) -> List[Dict]:'
)

# Line 553: docstring
content = content.replace(
    'List of outline items (may contain parts with pages or direct pages)',
    'List of outline items (may contain parts with pages or direct\n            pages)'
)

# Line 560: outline_json
content = content.replace(
    'outline_json = response_text.strip().strip(\"```json\").strip(\"```\").strip()',
    'outline_json = (\n            response_text.strip().strip(\"```json\").strip(\"```\").strip()\n        )'
)

# Line 564: parse_description_to_page_descriptions signature
content = content.replace(
    'def parse_description_to_page_descriptions(self, project_context: ProjectContext, outline: List[Dict]) -> List[str]:',
    'def parse_description_to_page_descriptions(\n        self, project_context: ProjectContext, outline: List[Dict]\n    ) -> List[str]:'
)

# Line 573: docstring
content = content.replace(
    'List of page descriptions (strings), one for each page in the outline',
    'List of page descriptions (strings), one for each page in the\n            outline'
)

# Line 580: descriptions_json
content = content.replace(
    'descriptions_json = response_text.strip().strip(\"```json\").strip(\"```\").strip()',
    'descriptions_json = (\n            response_text.strip().strip(\"```json\").strip(\"```\").strip()\n        )'
)

# Line 587: raise ValueError
content = content.replace(
    'raise ValueError(\"Expected a list of page descriptions, but got: \" + str(type(descriptions)))',
    'raise ValueError(\n                \"Expected a list of page descriptions, but got: \" +\n                str(type(descriptions))\n            )'
)

# Line 589: refine_outline signature
content = content.replace(
    'def refine_outline(self, current_outline: List[Dict], user_requirement: str,\n                      project_context: ProjectContext,\n                      previous_requirements: Optional[List[str]] = None) -> List[Dict]:',
    'def refine_outline(\n        self, current_outline: List[Dict], user_requirement: str,\n        project_context: ProjectContext,\n        previous_requirements: Optional[List[str]] = None\n    ) -> List[Dict]:'
)

# Line 591: docstring
content = content.replace(
    'previous_requirements: 之前的修改要求列表（可选）',
    'previous_requirements: 之前的修改要求列表（可选）'
) # No change needed?

# Line 614: outline_json
content = content.replace(
    'outline_json = response_text.strip().strip(\"```json\").strip(\"```\").strip()',
    'outline_json = (\n            response_text.strip().strip(\"```json\").strip(\"```\").strip()\n        )'
)

# Line 618: refine_descriptions signature
content = content.replace(
    'def refine_descriptions(self, current_descriptions: List[Dict], user_requirement: str,\n                           project_context: ProjectContext,\n                           outline: List[Dict] = None,\n                           previous_requirements: Optional[List[str]] = None) -> List[str]:',
    'def refine_descriptions(\n        self, current_descriptions: List[Dict], user_requirement: str,\n        project_context: ProjectContext,\n        outline: List[Dict] = None,\n        previous_requirements: Optional[List[str]] = None\n    ) -> List[str]:'
)

# Line 626: docstring
content = content.replace(
    'current_descriptions: 当前的页面描述列表，每个元素包含 {index, title, description_content}',
    'current_descriptions: 当前的页面描述列表，每个元素包含\n            {index, title, description_content}'
)

# Line 646: descriptions_json
content = content.replace(
    'descriptions_json = response_text.strip().strip(\"```json\").strip(\"```\").strip()',
    'descriptions_json = (\n            response_text.strip().strip(\"```json\").strip(\"```\").strip()\n        )'
)

# Line 653: raise ValueError
content = content.replace(
    'raise ValueError(\"Expected a list of page descriptions, but got: \" + str(type(descriptions)))',
    'raise ValueError(\n                \"Expected a list of page descriptions, but got: \" +\n                str(type(descriptions))\n            )'
)

# Ensure newline at end of file
if not content.endswith('\n'):
    content += '\n'

open(path, 'w', encoding='utf-8').write(content)
print(\"Successfully fixed lint errors in ai_service.py\")
