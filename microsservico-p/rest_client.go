package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type RestClient struct {
	addr   string
	client *http.Client
}

func NewRestClient(addr string) *RestClient {
	return &RestClient{
		addr: addr,
		client: &http.Client{
			Timeout: 15 * time.Second,
			Transport: &http.Transport{
				MaxIdleConns:        100,
				MaxIdleConnsPerHost: 100,
				IdleConnTimeout:     90 * time.Second,
			},
		},
	}
}

func (c *RestClient) get(path string, target interface{}) error {
	url := fmt.Sprintf("http://%s%s", c.addr, path)
	resp, err := c.client.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP %d: falha na requisição", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}

	return json.Unmarshal(body, target)
}

func (c *RestClient) post(path string, data interface{}, target interface{}) error {
	url := fmt.Sprintf("http://%s%s", c.addr, path)
	
	jsonData, err := json.Marshal(data)
	if err != nil {
		return err
	}

	resp, err := c.client.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP %d: falha na requisição", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}

	return json.Unmarshal(body, target)
}

func (c *RestClient) put(path string, data interface{}, target interface{}) error {
	url := fmt.Sprintf("http://%s%s", c.addr, path)
	jsonData, err := json.Marshal(data)
	if err != nil {
		return err
	}
	req, err := http.NewRequest(http.MethodPut, url, bytes.NewBuffer(jsonData))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := c.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP %d: falha na requisição", resp.StatusCode)
	}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	return json.Unmarshal(body, target)
}

func (c *RestClient) delete(path string, target interface{}) error {
	url := fmt.Sprintf("http://%s%s", c.addr, path)
	req, err := http.NewRequest(http.MethodDelete, url, nil)
	if err != nil {
		return err
	}
	resp, err := c.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP %d: falha na requisição", resp.StatusCode)
	}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	return json.Unmarshal(body, target)
}
