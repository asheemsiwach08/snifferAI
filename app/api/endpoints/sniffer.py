import yaml
from pathlib import Path
from urllib.parse import urlparse

import logging
from firecrawl import JsonConfig
from fastapi import APIRouter, HTTPException
from app.services.crawlers import firecrawler
from app.services.llm_services import openai_analyzer, gemini_service
from app.models.schemas import (
    SnifferAIRequest, SnifferAIResponse, SnifferExtractSchema, LendersGeminiSearchResponse, ClassificationAgentRequest, GenerateConfigAgentRequest, IOCLExtractSchema)
from app.utils.prompts import (refinement_prompt_v2, lenders_usecase_system_message_v2, lenders_usecase_prompt_v2)

from app.utils.prompts import get_prompt
from app.services.database_service import database_service
from app.services.sniffer_services import get_lenders_data
from app.services.llm_services import openai_analyzer

logger = logging.getLogger(__name__)


router = APIRouter()

keywords = ["interest","roi","mitc","term","condition","approved", "foir", "ltv", "lap", "home",
"roi", "house","salaried","employed","credit score","score","profession","borrower", "criteria","eligibility",
"property type", "property"]

def generate_output_format(output_format):
    """
    Generate a dynamic BaseModel class from the output_format list
    
    Args:
        output_format: List of TableColumns objects or dict with column_name and column_type
        
    Returns:
        BaseModel class: Dynamically created Pydantic BaseModel class
    """
    from pydantic import BaseModel, Field
    from typing import Optional, List, Dict, Any
    
    if not output_format:
        return None
        
    # Handle list of TableColumns objects or dictionaries
    if isinstance(output_format, list):
        fields = {}
        
        for item in output_format:
            # Handle both dict and TableColumns object
            if hasattr(item, 'column_name') and hasattr(item, 'column_type'):
                column_name = item.column_name
                column_type = item.column_type
            elif isinstance(item, dict):
                column_name = item.get("column_name")
                column_type = item.get("column_type")
            else:
                continue
                
            if column_name and column_type:
                # Map string types to Python types
                type_mapping = {
                    'str': str,
                    'string': str,
                    'int': int,
                    'integer': int,
                    'float': float,
                    'bool': bool,
                    'boolean': bool,
                    'list': List[str],
                    'dict': Dict[str, Any],
                    'optional_str': Optional[str],
                    'optional_int': Optional[int],
                    'optional_float': Optional[float],
                    'optional_bool': Optional[bool]
                }
                
                # Get the appropriate type, default to Optional[str] if not found
                field_type = type_mapping.get(column_type.lower(), Optional[str])
                
                # Create field with description
                fields[column_name] = (field_type, Field(None, description=f"The {column_name} field"))
        
        # Create dynamic BaseModel class
        if fields:
            # Convert fields to proper annotations format
            annotations = {}
            field_definitions = {}
            
            for field_name, (field_type, field_info) in fields.items():
                annotations[field_name] = field_type
                field_definitions[field_name] = field_info
            
            # Create the class dictionary with proper annotations
            class_dict = {
                '__annotations__': annotations,
                **field_definitions
            }
            
            DynamicModel = type('DynamicOutputModel', (BaseModel,), class_dict)
            return DynamicModel
    
    return None
        


def schema_match(schema):
    if schema == "LendersGeminiSearchResponse":
        return LendersGeminiSearchResponse
    elif schema == "SnifferExtractSchema":
        return SnifferExtractSchema
    elif schema == "IOCLExtractSchema":
        return IOCLExtractSchema
    else:
        return None

def add_entity_to_response(response: list[dict], entity: str, source: str = "sniffer"):
    if not isinstance(response, list):
        response = [response]

    # Add the entity to the response
    for record in response:
        record["entity"] = entity
        record["source"] = source
    return response


def find_empty_keys(data):
    empty_keys = []
    for key, value in data.items():
        if type(value) != list and (not value or value.lower() in ['n/a', None, "not found"]):
            empty_keys.append(key)
    return empty_keys


def dict_to_string(dictionary):
    string = ""
    for key, value in dictionary.items():
        string += f"KEY NAME: {key} -> KEY RELATED DATA: {value}\n"
    return string


def read_yaml(file_path):
    """
    Read and parse a YAML file
    
    Args:
        file_path (str): Path to YAML file
        
    Returns:
        dict: Parsed YAML content or None if error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def read_config():
    """
    Read config.yaml from project root
    
    Returns:
        dict: Configuration data
    """
    config_path = Path("config.yaml")
    return read_yaml(config_path)


########################################## Validators ##########################################
def validate_request_input(request: SnifferAIRequest):
    if not request.urls:
        raise HTTPException(status_code=400, detail="URLs are required - Please provide the URLs to scrape")
    if not request.googleSearch and not request.snifferTool:
        raise HTTPException(status_code=400, detail="Please enable google search or sniffer tool")
    return True


########################################### Sniffer AI ##########################################
@router.post("/sniffer_ai", response_model=SnifferAIResponse)
def sniffer_ai(request: SnifferAIRequest):
    logger.info(f"Received request to Sniffer AI - {request.urls}")

    # Validation Checks
    validate_request_input(request)

    # Global Variables
    update_if_exists = True

    ## Usecase loading ## --> Extract the configuration for the usecase
    config = read_config()
    all_usecases = config.get("use_cases", {})
    usecases = list(set(all_usecases.keys()))
    print("USecases: ", usecases)
    breakpoint()

    ###################################### Classicfication Agent ##############################################
    schema_keywords = usecases + ["Not Found"]

    messages = [{"role": "system", 
    "content": f"""You are a helpful assistant whose task is to classify the data based on the keywords provided.
        Keywords provided: {schema_keywords}
        You have to select only one keyword matching the urls or details provided to you by the user, if you are
        not able to find any matching keyword, then select the 'Not Found' keyword.""", 
    }, 
    {"role": "user", 
    "content": f"""Classify the data based on the urls or details provided to you by the user.
    URLS:  {request.urls}
    Details:  {request.prompt}"""}]
    
    # CA.1 --> Classification Agent
    classification_agent_response = openai_analyzer.analyze_context(model="gpt-4o-mini",messages=messages, response_format=ClassificationAgentRequest)
    classification_agent_response = classification_agent_response.get("data", {})
    logger.info(f"Classification agent response: {classification_agent_response}")

    # CA.2 --> Classification Agent Response
    if classification_agent_response:
        entity = classification_agent_response.get("entity", None)
        usecase = classification_agent_response.get("keyword", None)
        logger.info(f"Classification agent response is classified, entity: {entity}, usecase: {usecase}")
        breakpoint()

    # CA.3 --> Usecase Identification
    try:
        # Convert schema_keywords to lowercase for comparison
        schema_keywords_lower = [keyword.lower() for keyword in schema_keywords]
        
        if usecase and usecase.lower() in schema_keywords_lower:
            classified_usecase = usecase
        else:
            classified_usecase = "Not Found"
    except Exception as e:
        logger.error(f"Error in usecase identification: {e}")
        classified_usecase = "Not Found"


    # CA.4.1 --> Usecase Identification
    if classified_usecase != "Not Found":
        logger.info("Usecase is found in our system config")
        try:
            usecase_config = all_usecases.get(classified_usecase.lower(), {})

            # CA.4.1.1 --> If the usecase config is empty, use the default config
            if len(usecase_config) == 0:
                usecase_config = all_usecases.get("default", {}) # TODO: Change this - using Not Found in keywords in classification agent.
            
            # CA.4.1.2 --> Extract the configuration for the usecase
            logger.info(f"Loading usecase config for {classified_usecase}.")
            keywords = usecase_config.get("keywords", [])
            unique_key = usecase_config.get("unique_key", "id")
            table_name = usecase_config.get("table_name", "table")
            update_if_exists = usecase_config.get("update_if_exists", True)
            config_output_format = usecase_config.get("output_format", "LendersGeminiSearchResponse")   # TODO: Change this to another default format

            scraper_system_message = usecase_config.get("scraper_system_message", "")
            scraper_prompt = usecase_config.get("scraper_prompt", "")
            refinement_prompt = usecase_config.get("refinement_prompt", "")

            # CA.4.1.3 --> Model Schema
            try:
                model_schema = schema_match(config_output_format)
            except Exception as e:
                logger.error(f"Failed to match schema: {e}")
                model_schema = schema_match("SnifferExtractSchema")

            logger.info(f"Output format: {config_output_format}")
            logger.info(f"Usecase config loaded successfully.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid usecase: {e}")
        
    # CA.4.2 --> Usecase Generation
    elif classified_usecase == "Not Found":
        logger.info("Classification agent response is not classified, generating config for the usecase")
        messages = [
            {"role": "system", 
            "content": """You are a helpful assistant which can generate the config for the usecase based on the 
            urls or details provided to you by the user.""", 
        }, 
        {"role": "user", "content": f"Generate the config for the usecase based on the urls or details provided to you by the user. URLS: {request.urls} Details: {request.prompt}"
        }]

        # CA.4.2.1 --> Config Generation Agent
        config_generation_agent = openai_analyzer.analyze_context(model="gpt-4o-mini",messages=messages, response_format=GenerateConfigAgentRequest)
        config_generation_agent = config_generation_agent.get("data", {})
        logger.info(f"Config generation agent response: {config_generation_agent}")

        # CA.4.2.2 --> Config Generation Agent Response
        if config_generation_agent:
            entity = config_generation_agent.get("entity", None)
            usecase = config_generation_agent.get("usecase", None)
            keywords = config_generation_agent.get("keywords", None)
            table_name = config_generation_agent.get("table_name", None)
            unique_key = config_generation_agent.get("unique_key", None)
            output_format = config_generation_agent.get("output_format", None)
            scraper_prompt = config_generation_agent.get("scraper_prompt", None)
            refinement_prompt = config_generation_agent.get("refinement_prompt", None)
            scraper_system_message = config_generation_agent.get("scraper_system_message", None)

            # CA.4.2.3 --> Generate dynamic BaseModel class from output_format
            if output_format:
                model_schema = generate_output_format(output_format)
                if model_schema:
                    logger.info(f"Dynamic model schema generated successfully from output_format")
                else:
                    logger.warning("Failed to generate dynamic model schema, falling back to default")
                    model_schema = schema_match("SnifferExtractSchema")  # fallback to default schema


            breakpoint()

        else:
            raise HTTPException(status_code=400, detail="Invalid config generation agent response")

    else:
        raise HTTPException(status_code=400, detail="Invalid classification agent response")

    logger.info("Direeeeeeeeeeeeeeeeeeee")
    breakpoint()

    print("Model Schema: ", model_schema)
    breakpoint()

    ########################################## Input Gathering #########################################
    # IG.1 --> Input Gathering
    if request.urls:
        urls = request.urls
        domain = urlparse(urls[0]).netloc

    # IG.2 --> Input Gathering
    if request.keywordsToSearch:
        keywords = keywords + request.keywordsToSearch  # TODO: Need to add this to the all the tools for better reachability

    logger.info("All the inputs gathered. Lets start the process.")

    #################################### Prompt Loading #######################################################
    if classified_usecase != "Not Found":
        get_scraper_system_message = get_prompt(scraper_system_message)
        get_scraper_prompt = get_prompt(scraper_prompt)
        get_refinement_prompt = get_prompt(refinement_prompt)

        if not get_scraper_system_message:
            scraper_system_message = get_scraper_system_message.format(domain_allowlist=str(domain))

        if not get_scraper_prompt:
            scraper_prompt = get_scraper_prompt.format(lender_name=domain, lender_website=str(domain), domain_allowlist=str(domain))
        
        final_scraper_prompt = scraper_system_message + "\n" + scraper_prompt + request.prompt
    elif classified_usecase == "Not Found":
        final_scraper_prompt = scraper_system_message + "\n" + scraper_prompt
    
    print("Final Scraper Prompt: ", final_scraper_prompt)
    breakpoint()

    #################################### Custom Scraper: Lenders Data #########################################
    # if request.dataToExtract.lower() == "lenders":
    #     logger.info("Extracting data from Lenders - using custom scraper")
    #     custom_scraper_response = get_lenders_data(url=request.url, multiple_urls=request.multipleUrls, keywords=keywords)
    #     first_tool_response = custom_scraper_response.get("data", {})

    ################################################## SnifferBase Agents #################################################
    
    # SBA.1.1 --> Google Search Agent
    if request.googleSearch:
        logger.info("Extracting data - using google search tool")
        search_prompt = get_prompt("gemini_search_prompt")
        search_prompt = search_prompt.format(source=domain)
        first_tool_response = gemini_service.search_google(search_prompt, model="gemini-2.0-flash")
        # print("---------------------------------SEARCH RESPONSE---------------------------------")
        # print(first_tool_response)
        # print("---------------------------------SEARCH RESPONSE ENDS---------------------------------")

    # SBA.1.2 --> Data Extraction Agent
    elif request.snifferTool:
        logger.info("Extracting data - using sniffer tool")
        first_tool_response  = firecrawler.extract_data(urls=request.urls, prompt=final_scraper_prompt, schema=model_schema.model_json_schema())
        print("---------------------------------SCRAPER RESPONSE--------------------------------------")
        print(request.urls,"<<<--------------->>>",first_tool_response)
        print("---------------------------------SCRAPER RESPONSE ENDS---------------------------------")
    
    # SBA.1.3 --> Error Handling
    else:
        logger.info("No tool selected")
        raise HTTPException(status_code=400, detail="No tool selected")

    if isinstance(first_tool_response, dict):
        try:
            first_tool_response = first_tool_response.get("data", {})
            if "output" in first_tool_response.keys():
                first_tool_response = first_tool_response.get("output", {})
            
            if isinstance(first_tool_response, list) and len(first_tool_response) == 0:
                print(":::::::::::::::",request.urls)
                logger.error(f"No data found in the first tool response - {first_tool_response}")
                raise HTTPException(status_code=400, detail="No data found in the first tool response")
            
            # TODO: Change/Add the source to the actual source
            first_tool_response = add_entity_to_response(first_tool_response, entity, source=domain)  
        except Exception as e:
            logger.error(f"Failed to extract data from scraper: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to extract data from scraper: {e}")

        logger.info("---FIRST TOOL RESPONDED")

    else:
        logger.error(f"Failed to scrape data from the tool: {first_tool_response}")
        raise HTTPException(status_code=400, detail="Failed to scrape data from the tool")

    print("---------------------------------FIRST TOOL RESPONSE ENDs---------------------------------")
    ################################################# Tool 2 #################################################
    # Go forward with the search mode if enabled
    if request.snifferTool and request.enableSearch:
        logger.info("Using sniffer tool for search also")
        if first_tool_response:
            # Check if the first response has any empty keys
            if isinstance(first_tool_response, list):
                logger.info("Upcoming feature: Search for the empty keys in the list")
                pass
            elif isinstance(first_tool_response, dict):
                empty_keys = find_empty_keys(first_tool_response)
                if empty_keys:
                    logger.info(f"------------------------------------------ \nEmpty keys: {empty_keys}")
                # Search for the empty keys
                # for key in empty_keys:
                input_data = " ".join(empty_keys)
                key_search_response = firecrawler.search_data(input_data=input_data)
                print("---------------------------------KEY SEARCH RESPONSE---------------------------------")
                first_tool_response["other_data"] = str(key_search_response.get("data", {}))
                second_tool_response = first_tool_response
            else:
                second_tool_response = first_tool_response
                logger.info("No empty keys found")

        logger.info("---SECOND TOOL RESPONDED")

    else:
        second_tool_response = first_tool_response

    print("---------------------------------SECOND TOOL RESPONSE ENDS---------------------------------")
    ################################################## Tool 3 #################################################
    # Go forward with the refinement mode if enabled
    if request.enableRefinement:
        logger.info("Refinement mode enabled")
        # Check if the search response is empty
        if not second_tool_response:
            logger.error("No records found for refinement process")
            raise HTTPException(status_code=400, detail="No records found for refinement process")

        try:
            # Format the search response to a string
            formatted_dict = dict_to_string(second_tool_response)
            cleaned_string = formatted_dict.replace("{", '(').replace("}", ')')
            
            # Model Inititaion and prompting
            logger.info("Moving to refinement process")
            get_refinement_prompt = get_prompt(refinement_prompt)
            if not get_refinement_prompt:
                refinement_prompt = get_refinement_prompt.format(str(cleaned_string))
            else:
                refinement_prompt = refinement_prompt + f"\nData: {str(cleaned_string)}"

            # refinementprompt = refinement_prompt.format(str(cleaned_string))
            print("Refinement prompt: ", refinement_prompt)

            # Structured Response
            refinement_response = openai_analyzer.structured_output(
                prompt=f"Please refine the data - {cleaned_string}",
                response_format=model_schema,
                model="gpt-4o-2024-08-06"
            )
            
            if refinement_response:
                final_response = refinement_response.get("data", {})
                logger.info(f"Parsed response: {final_response}")
            else:
                logger.error("No response from refinement process")
                raise HTTPException(status_code=400, detail="No response from refinement process")
        except Exception as e:
            logger.error(f"Failed to refine data: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to refine data: {e}")

        logger.info("---THIRD TOOL RESPONDED")

    else:
        final_response = second_tool_response

    print("---------------------------------THIRD TOOL RESPONSE ENDS---------------------------------")
    ################################################ Saving to Database #############################################
    print("Final Response: ", final_response)
    breakpoint()
    if not final_response:
        logger.error("No records found for refinement process")
        raise HTTPException(status_code=400, detail="No records found for refinement process")

    try:
        # Convert the final response to a list if it is not already otherwise need to separate for each record
        if not isinstance(final_response, list):
            final_response = [final_response]
            
        column_names = list(final_response[0].keys())
        print("Column names: ", column_names)
        breakpoint()

        table_check = database_service.check_table_exists(table_name)
        print("Table check: ", table_check)
        print("Table name: ", table_name)
        print("Unique key: ", unique_key)
        print("Column names: ", column_names)
        breakpoint()

        if not table_check:
            create_table_result = database_service.create_table_from_columns(column_names, table_name, unique_key)
            logger.info(f"Create table result: {create_table_result}")
            if create_table_result["status"] == "error":
                logger.error(f"Failed to generate sql table quert: {create_table_result['message']}")
                raise HTTPException(status_code=400, detail=f"Failed to generate sql table query: {create_table_result['message']}")
            else:
                generate_table_result = database_service.execute_sql_command(create_table_result["sql"])
                logger.info(f"Generate table result: {generate_table_result}")
                if generate_table_result["status"] == "error":
                    logger.error(f"Failed to generate sql table query: {generate_table_result['message']}")
                    raise HTTPException(status_code=400, detail=f"Failed to generate sql table query: {generate_table_result['message']}")
                else:
                    logger.info(f"Table {table_name} created successfully")

        else:
            logger.info(f"Table {table_name} already exists")

        # database_service.save_unique_data(scrape_result.data, table_name, primary_key, update_if_exists=update_if_exists) 
        database_save_result = database_service.save_batch_unique_data(final_response, table_name, primary_key, update_if_exists=update_if_exists) 
        logger.info(f"Database save result: {database_save_result}")

        # # Use the interactive table creation approach
        # result = database_service.interactive_save_with_table_creation(
        #     data_list=final_response, 
        #     table_name=table_name, 
        #     primary_key=primary_key, 
        #     update_if_exists=update_if_exists,
        #     column_names=column_names
        # )
        

        logger.info("--DATA SAVED TO DATABASE")
    except Exception as e:
        logger.error(f"Failed to save data to database: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to save data to database: {e}")

    print("******************* FINAL RESPONSE ENDS *****************************")

    return SnifferAIResponse(success=True, message="We are in the last.")
